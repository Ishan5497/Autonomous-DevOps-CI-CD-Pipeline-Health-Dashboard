import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import SessionLocal, init_db, engine, Base
from backend.models.entities import PipelineRun, PullRequest, SecurityFinding, WebhookEvent
from backend.services.pipeline_health import PipelineHealthService
from backend.services.static_analysis import StaticAnalysisService

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield


# ==========================================
# 1. Pipeline Router Tests
# ==========================================

def test_pipeline_runs_filtering_and_retrieval():
    # Insert multiple runs with different statuses
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        r1 = PipelineRun(
            pipeline_id="pipe-filter-1",
            repository="test/repo",
            branch="main",
            commit_sha="111111",
            commit_message="feat: one",
            author="dev1",
            status="success",
            stage="deploy",
            duration_seconds=30.0,
            created_at=now - timedelta(minutes=5),
        )
        r2 = PipelineRun(
            pipeline_id="pipe-filter-2",
            repository="test/repo",
            branch="feature/test",
            commit_sha="222222",
            commit_message="fix: two",
            author="dev2",
            status="failed",
            stage="test",
            duration_seconds=15.0,
            failure_reason="Assertion failed",
            created_at=now - timedelta(minutes=2),
        )
        db.add_all([r1, r2])
        db.commit()

    # List all
    res = client.get("/api/v1/pipeline/runs")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2

    # Filter by status
    res = client.get("/api/v1/pipeline/runs?status=failed")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["pipeline_id"] == "pipe-filter-2"

    # Filter by branch
    res = client.get("/api/v1/pipeline/runs?branch=main")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["branch"] == "main"

    # Get single run by ID
    res = client.get("/api/v1/pipeline/runs/pipe-filter-1")
    assert res.status_code == 200
    assert res.json()["pipeline_id"] == "pipe-filter-1"
    assert res.json()["status"] == "success"

    # Get non-existent run
    res = client.get("/api/v1/pipeline/runs/non-existent-id")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_pipeline_runs_create_endpoint():
    payload = {
        "repository": "test/repo",
        "pipeline_id": "pipe-created-via-post",
        "branch": "staging",
        "commit_sha": "abcdef123456",
        "commit_message": "ci: trigger pipeline run",
        "author": "ci-bot",
        "status": "running",
        "stage": "build",
        "duration_seconds": 12.0,
    }
    res = client.post("/api/v1/pipeline/runs", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["pipeline_id"] == "pipe-created-via-post"


def test_pipeline_recommendations_and_health():
    res = client.get("/api/v1/pipeline/recommendations")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    res = client.get("/api/v1/pipeline/health")
    assert res.status_code == 200
    data = res.json()
    assert "health_grade" in data
    assert "risk_level" in data
    assert "recommendations" in data


def test_pull_requests_endpoint():
    with SessionLocal() as db:
        pr1 = PullRequest(
            repository="test/repo",
            pr_number=1,
            title="feat: pr one",
            state="open",
            action="opened",
            author="dev",
        )
        pr2 = PullRequest(
            repository="test/repo",
            pr_number=2,
            title="fix: pr two",
            state="merged",
            action="closed",
            author="dev",
        )
        db.add_all([pr1, pr2])
        db.commit()

    res = client.get("/api/v1/pipeline/pull-requests")
    assert res.status_code == 200
    assert len(res.json()) == 2

    # Filter by state
    res = client.get("/api/v1/pipeline/pull-requests?state=open")
    assert res.status_code == 200
    assert len(res.json()) == 1
    assert res.json()[0]["pr_number"] == 1


# ==========================================
# 2. Security Router Tests
# ==========================================

def test_scan_diff_with_persistence():
    diff_with_secret = (
        "diff --git a/app.py b/app.py\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1,1 +1,2 @@\n"
        "+SLACK_URL = 'https://hooks.slack.com/services/YOUR/DUMMY/WEBHOOK'\n"
    )
    res = client.post(
        "/api/v1/security/scan-diff?persist=true",
        json={
            "diff": diff_with_secret,
            "file_path": "app.py",
            "repository": "test/repo",
            "commit_sha": "sec1234",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_safe"] is False
    assert data["findings_count"] >= 1

    # Verify persisted findings in DB
    findings_res = client.get("/api/v1/security/findings")
    assert findings_res.status_code == 200
    persisted = findings_res.json()
    assert len(persisted) >= 1
    finding_id = persisted[0]["id"]

    # Filter by severity
    crit_res = client.get("/api/v1/security/findings?severity=CRITICAL")
    assert crit_res.status_code == 200

    # Filter by repository
    repo_res = client.get("/api/v1/security/findings?repository=test/repo")
    assert repo_res.status_code == 200
    assert len(repo_res.json()) >= 1

    # Resolve / Delete finding
    del_res = client.delete(f"/api/v1/security/findings/{finding_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Delete non-existent finding
    del_res_404 = client.delete(f"/api/v1/security/findings/999999")
    assert del_res_404.status_code == 404


def test_security_rules_endpoint():
    res = client.get("/api/v1/security/rules")
    assert res.status_code == 200
    data = res.json()
    assert data["secret_rules_count"] > 0
    assert data["bug_rules_count"] > 0
    assert "secret_rules" in data
    assert "bug_rules" in data


# ==========================================
# 3. Dashboard Router Tests
# ==========================================

def test_seed_demo_data_lifecycle():
    # When runs < 5, seed should succeed
    res = client.post("/api/v1/dashboard/seed-demo-data")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert "seeded" in res.json()["message"].lower()

    # Second call should skip seeding since count >= 5
    res2 = client.post("/api/v1/dashboard/seed-demo-data")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ok"
    assert "skipping" in res2.json()["message"].lower()

    # Check dashboard summary incorporates seeded data
    summary = client.get("/api/v1/dashboard/summary").json()
    assert summary["health"]["total_runs"] >= 5
    assert len(summary["recent_runs"]) >= 5
    assert len(summary["recent_pull_requests"]) >= 2
    assert summary["system_status"]["status"] == "OPERATIONAL"


# ==========================================
# 4. Webhook Router & Service Edge Cases
# ==========================================

def test_webhook_invalid_json_payloads():
    # Send non-JSON raw body to github endpoint
    res = client.post(
        "/api/v1/webhooks/github",
        content="not-valid-json{{{",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 400
    assert "Invalid JSON payload" in res.json()["detail"]

    # Send non-JSON raw body to gitlab endpoint
    res2 = client.post(
        "/api/v1/webhooks/gitlab",
        content="not-valid-json{{{",
        headers={"Content-Type": "application/json"},
    )
    assert res2.status_code == 400
    assert "Invalid JSON payload" in res2.json()["detail"]


def test_github_webhook_pull_request_with_diff():
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 88,
            "title": "feat: security leak PR",
            "user": {"login": "octocat"},
            "head": {"ref": "feature/leak", "sha": "leak99999"},
            "base": {"ref": "main"},
            "diff": "+++ b/secret.py\n+GITHUB_PAT = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'\n",
        },
        "repository": {"full_name": "org/repo"},
        "sender": {"login": "octocat"},
    }
    headers = {"X-GitHub-Event": "pull_request"}
    res = client.post("/api/v1/webhooks/github", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["pr_number"] == 88
    assert data["static_analysis"] is not None
    assert data["static_analysis"]["critical_count"] >= 1

    # Re-trigger with action synchronize (updates existing PR)
    payload["action"] = "synchronize"
    res2 = client.post("/api/v1/webhooks/github", json=payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["status"] == "success"


def test_github_webhook_workflow_and_check_runs():
    # Workflow run failure
    wf_payload = {
        "workflow_run": {
            "id": "wf-999",
            "status": "completed",
            "conclusion": "failure",
            "head_branch": "main",
            "head_sha": "abc999",
            "display_title": "CI Test Suite",
            "run_duration_ms": 45000,
        },
        "repository": {"full_name": "org/repo"},
        "sender": {"login": "ci-bot"},
    }
    res = client.post(
        "/api/v1/webhooks/github",
        json=wf_payload,
        headers={"X-GitHub-Event": "workflow_run"},
    )
    assert res.status_code == 200
    assert res.json()["build_status"] == "failed"

    # Check run in progress
    check_payload = {
        "check_run": {
            "id": "chk-111",
            "status": "in_progress",
            "conclusion": None,
            "head_branch": "main",
            "head_sha": "abc111",
            "display_title": "Lint Gate",
        },
        "repository": {"full_name": "org/repo"},
        "sender": {"login": "ci-bot"},
    }
    res = client.post(
        "/api/v1/webhooks/github",
        json=check_payload,
        headers={"X-GitHub-Event": "check_run"},
    )
    assert res.status_code == 200
    assert res.json()["build_status"] == "running"


def test_github_webhook_unknown_event():
    res = client.post(
        "/api/v1/webhooks/github",
        json={"zen": "Non-code event"},
        headers={"X-GitHub-Event": "ping"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "acknowledged"


def test_gitlab_webhook_push_with_diff():
    payload = {
        "object_kind": "push",
        "project": {"path_with_namespace": "gitlab-org/project"},
        "user_name": "gitlab-user",
        "ref": "refs/heads/feature/branch",
        "after": "glcommit123",
        "commits": [{"id": "glcommit123", "message": "feat: test"}],
        "diff": "+++ b/config.py\n+GITLAB_PAT = 'glpat-1234567890abcdefghij'\n",
    }
    headers = {"X-Gitlab-Event": "Push Hook"}
    res = client.post("/api/v1/webhooks/gitlab", json=payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    assert res.json()["static_analysis"] is not None


def test_gitlab_webhook_pipeline_transitions():
    # Initial pipeline running
    pipe_payload = {
        "object_kind": "pipeline",
        "project": {"path_with_namespace": "gitlab-org/project"},
        "user_name": "gitlab-user",
        "object_attributes": {
            "id": 7788,
            "status": "running",
            "duration": 12.0,
            "ref": "main",
            "sha": "glsha77",
        },
    }
    headers = {"X-Gitlab-Event": "Pipeline Hook"}
    res = client.post("/api/v1/webhooks/gitlab", json=pipe_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["build_status"] == "running"

    # Transition pipeline to success
    pipe_payload["object_attributes"]["status"] = "success"
    pipe_payload["object_attributes"]["duration"] = 45.0
    res2 = client.post("/api/v1/webhooks/gitlab", json=pipe_payload, headers=headers)
    assert res2.status_code == 200
    assert res2.json()["build_status"] == "success"


def test_gitlab_webhook_unknown_event():
    res = client.post(
        "/api/v1/webhooks/gitlab",
        json={"event_name": "wiki_page"},
        headers={"X-Gitlab-Event": "Wiki Page Hook"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "acknowledged"


def test_webhooks_list_events_endpoint():
    # Trigger push and PR to generate events
    client.post(
        "/api/v1/webhooks/simulate/push",
        json={
            "repository": "test/repo",
            "commit_sha": "eventsha1",
            "commit_message": "test events",
        },
    )
    res = client.get("/api/v1/webhooks/events?source=simulated&limit=10")
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 1
    assert events[0]["source"] == "simulated"


# ==========================================
# 5. Pipeline Health Metrics & MTTR Edge Cases
# ==========================================

def test_pipeline_health_calculation_branches():
    # Case 1: Empty database
    with SessionLocal() as db:
        empty_health = PipelineHealthService.calculate_health(db)
        assert empty_health.total_runs == 0
        assert empty_health.success_rate_percent == 100.0
        assert empty_health.health_grade == "A"
        assert empty_health.mttr_display == "Optimal (0 failures / instant)"

    # Case 2: MTTR with failed run recovered by success
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        r_fail = PipelineRun(
            pipeline_id="r-fail",
            repository="repo",
            branch="main",
            status="failed",
            duration_seconds=20.0,
            created_at=now - timedelta(minutes=10),
        )
        r_succ = PipelineRun(
            pipeline_id="r-succ",
            repository="repo",
            branch="main",
            status="success",
            duration_seconds=400.0,  # average (20 + 400) / 2 = 210s triggers performance recommendation (>180s)
            created_at=now - timedelta(minutes=5),
        )
        db.add_all([r_fail, r_succ])
        db.commit()

        health = PipelineHealthService.calculate_health(db)
        assert health.total_runs == 2
        assert health.failed_runs == 1
        assert health.successful_runs == 1
        assert health.mttr_seconds > 0
        assert "min" in health.mttr_display or "sec" in health.mttr_display
        # Should have performance recommendation (>180s)
        rec_types = [rec.type for rec in health.recommendations]
        assert "PERFORMANCE_OPTIMIZATION" in rec_types


def test_pipeline_health_grades_and_risks():
    with SessionLocal() as db:
        now = datetime.now(timezone.utc)
        # 10 runs, 5 failed -> 50% failure rate -> Grade F, CRITICAL
        runs = [
            PipelineRun(
                pipeline_id=f"r-{i}",
                repository="repo",
                branch="main",
                status="failed" if i < 5 else "success",
                duration_seconds=25.0,
                created_at=now - timedelta(minutes=i),
            )
            for i in range(10)
        ]
        db.add_all(runs)
        db.commit()

        health = PipelineHealthService.calculate_health(db)
        assert health.health_grade == "F"
        assert health.risk_level == "CRITICAL"
        rec_types = [rec.type for rec in health.recommendations]
        assert "PIPELINE_FIX" in rec_types
