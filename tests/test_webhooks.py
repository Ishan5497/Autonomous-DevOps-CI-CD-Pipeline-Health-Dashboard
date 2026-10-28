import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import Base, engine, init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "endpoints" in data


def test_simulate_push_clean():
    payload = {
        "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
        "ref": "refs/heads/main",
        "commit_sha": "abc1234567890",
        "commit_message": "docs: update architecture diagram",
        "author": "developer@example.com",
    }
    response = client.post("/api/v1/webhooks/simulate/push", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["pipeline_status"] == "success"


def test_simulate_push_with_secret_fails_pipeline():
    payload = {
        "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
        "ref": "refs/heads/main",
        "commit_sha": "badcommit999",
        "commit_message": "test: add bad config",
        "author": "attacker@example.com",
        "diff": """
--- a/config.py
+++ b/config.py
@@ -1,1 +1,1 @@
+AWS_KEY = "AKIA1111111111EXAMPLE"
""",
    }
    response = client.post("/api/v1/webhooks/simulate/push", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["pipeline_status"] == "failed"
    assert data["static_analysis"] is not None
    assert data["static_analysis"]["critical_count"] >= 1


def test_simulate_pull_request():
    payload = {
        "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
        "pr_number": 77,
        "title": "feat: autonomous healing for failing nodes",
        "action": "opened",
        "author": "ishan-dev",
        "head_branch": "feature/healing",
        "base_branch": "main",
        "head_sha": "f1e2d3c4b5a6",
    }
    response = client.post("/api/v1/webhooks/simulate/pull-request", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["pr_number"] == 77


def test_simulate_build_status():
    payload = {
        "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
        "pipeline_id": "pipe-build-001",
        "branch": "main",
        "commit_sha": "f1e2d3c4b5a6",
        "status": "success",
        "stage": "deploy",
        "duration_seconds": 42.0,
    }
    response = client.post("/api/v1/webhooks/simulate/build-status", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["pipeline_id"] == "pipe-build-001"


def test_github_webhook_receiver():
    github_payload = {
        "repository": {
            "full_name": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
            "name": "Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
        },
        "sender": {"login": "octocat"},
        "ref": "refs/heads/main",
        "head_commit": {
            "id": "1234567890abcdef",
            "message": "ci: trigger pipeline run",
            "author": {"name": "octocat"},
        },
        "commits": [],
    }
    headers = {
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "delivery-guid-123",
    }
    response = client.post("/api/v1/webhooks/github", json=github_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_gitlab_webhook_receiver():
    gitlab_payload = {
        "object_kind": "push",
        "project": {
            "path_with_namespace": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
            "name": "Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
        },
        "user_name": "gitlab-ci-bot",
        "ref": "refs/heads/main",
        "after": "abcdef1234567890",
        "commits": [
            {"id": "abcdef1234567890", "message": "chore: dependency update"}
        ],
    }
    headers = {
        "X-Gitlab-Event": "Push Hook",
    }
    response = client.post("/api/v1/webhooks/gitlab", json=gitlab_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
