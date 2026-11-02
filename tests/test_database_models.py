import pytest
from datetime import datetime, timezone
from backend.models.database import SessionLocal, init_db, engine, Base
from backend.models.entities import WebhookEvent, PipelineRun, PullRequest, SecurityFinding
from backend.services.static_analysis import StaticAnalysisService


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    init_db()
    yield


def test_webhook_event_entity_defaults():
    with SessionLocal() as db:
        event = WebhookEvent(
            source="github",
            event_type="push",
            payload='{"commits": []}',
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        assert event.id is not None
        assert event.status == "processed"
        assert event.created_at is not None
        assert event.source == "github"
        assert event.event_type == "push"


def test_pipeline_run_entity_fields():
    with SessionLocal() as db:
        run = PipelineRun(
            pipeline_id="pipe-entity-test",
            repository="org/repo",
            branch="staging",
            commit_sha="abcdef1234567890",
            commit_message="test commit",
            author="tester",
            status="running",
            stage="test",
            duration_seconds=42.5,
            failure_reason=None,
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        assert run.id is not None
        assert run.pipeline_id == "pipe-entity-test"
        assert run.branch == "staging"
        assert run.duration_seconds == 42.5
        assert run.started_at is not None


def test_pull_request_entity_lifecycle():
    with SessionLocal() as db:
        pr = PullRequest(
            repository="org/repo",
            pr_number=42,
            title="feat: automated test entity",
            state="open",
            action="opened",
            author="alice",
            head_branch="feature/x",
            base_branch="main",
            head_sha="head1234",
        )
        db.add(pr)
        db.commit()
        db.refresh(pr)

        assert pr.id is not None
        assert pr.pr_number == 42
        assert pr.state == "open"
        assert pr.created_at is not None
        assert pr.updated_at is not None


def test_security_finding_entity_creation():
    with SessionLocal() as db:
        finding = SecurityFinding(
            repository="org/repo",
            commit_sha="sha999",
            file_path="src/config.py",
            line_number=12,
            rule_id="SEC-001",
            rule_name="AWS Access Key ID",
            issue_type="HARDCODED_SECRET",
            severity="CRITICAL",
            description="Leaked AWS access key detected.",
            snippet_redacted="AKIA****************LE",
            recommendation="Revoke secret immediately.",
        )
        db.add(finding)
        db.commit()
        db.refresh(finding)

        assert finding.id is not None
        assert finding.severity == "CRITICAL"
        assert finding.issue_type == "HARDCODED_SECRET"
        assert finding.created_at is not None


# ==========================================
# Comprehensive Static Analysis Rules Tests
# ==========================================

def test_static_analysis_private_key_detection():
    diff = """
+++ b/keys/server.key
+-----BEGIN RSA PRIVATE KEY-----
+MIIEowIBAAKCAQEA0Y1+
+-----END RSA PRIVATE KEY-----
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert not result.is_safe
    rule_ids = [f.rule_id for f in result.findings]
    assert "SEC-006" in rule_ids


def test_static_analysis_generic_api_key_and_jwt():
    diff = """
+++ b/client.py
+api_key = "1234567890abcdef1234567890abcdef"
+bearer_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert not result.is_safe
    rule_ids = [f.rule_id for f in result.findings]
    assert "SEC-007" in rule_ids or "SEC-009" in rule_ids


def test_static_analysis_database_connection_string():
    diff = """
+++ b/settings.py
+DATABASE_URI = "postgres://admin:SuperSecretPass123@prod-db.internal:5432/core"
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert not result.is_safe
    rule_ids = [f.rule_id for f in result.findings]
    assert "SEC-008" in rule_ids


def test_static_analysis_insecure_tls_and_random():
    diff = """
+++ b/service.py
+response = requests.get("https://internal.service", verify=False)
+token = random.random()
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert not result.is_safe
    rule_ids = [f.rule_id for f in result.findings]
    assert "BUG-003" in rule_ids  # Disabled TLS
    assert "BUG-004" in rule_ids  # Insecure random generator


def test_static_analysis_silent_except_and_exec():
    diff = """
+++ b/worker.py
+eval(user_supplied_str)
+except: pass
"""
    result = StaticAnalysisService.scan_diff(diff)
    assert not result.is_safe
    rule_ids = [f.rule_id for f in result.findings]
    assert "BUG-001" in rule_ids  # exec/eval
    assert "BUG-005" in rule_ids  # silent exception
