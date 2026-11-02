import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_websocket_status_endpoint():
    response = client.get("/api/v1/ws/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "active_clients" in data
    assert data["endpoint"] == "/api/v1/ws"


def test_websocket_handshake_and_ping():
    with client.websocket_connect("/api/v1/ws") as ws:
        # First message is connection handshake
        handshake = ws.receive_json()
        assert handshake["type"] == "CONNECTION_ESTABLISHED"
        assert "metrics" in handshake
        assert "timestamp" in handshake

        # Ping-pong text test
        ws.send_text("ping")
        reply = ws.receive_text()
        assert reply == "pong"

        # Action: get_metrics
        ws.send_json({"action": "get_metrics"})
        metrics_msg = ws.receive_json()
        assert metrics_msg["type"] == "METRICS_UPDATE"
        assert "metrics" in metrics_msg


def test_websocket_broadcasts_pipeline_update():
    with client.websocket_connect("/api/v1/ws") as ws:
        # Discard handshake
        _ = ws.receive_json()

        # Fire a simulated clean push
        payload = {
            "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
            "ref": "refs/heads/feature/real-time",
            "commit_sha": "a1b2c3d4e5f6",
            "commit_message": "feat: real-time websocket broadcast",
            "author": "ishan-dev",
        }
        res = client.post("/api/v1/webhooks/simulate/push", json=payload)
        assert res.status_code == 200

        # Receive broadcast on websocket
        event = ws.receive_json()
        assert event["type"] == "PIPELINE_UPDATE"
        assert event["data"]["commit_sha"] == "a1b2c3d4e5f6"
        assert event["data"]["status"] == "success"
        assert "metrics" in event


def test_websocket_broadcasts_security_alert_and_build_failure():
    with client.websocket_connect("/api/v1/ws") as ws:
        # Discard handshake
        _ = ws.receive_json()

        # Fire a simulated push with hardcoded AWS secret
        payload = {
            "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
            "ref": "refs/heads/main",
            "commit_sha": "secfail9999",
            "commit_message": "fix: critical secret leak",
            "author": "attacker",
            "diff": "--- a/keys.py\n+++ b/keys.py\n@@ -1 +1 @@\n+AWS_KEY = 'AKIA1111111111EXAMPLE'\n",
        }
        res = client.post("/api/v1/webhooks/simulate/push", json=payload)
        assert res.status_code == 200

        # Receive BUILD_FAILURE broadcast
        fail_event = ws.receive_json()
        assert fail_event["type"] == "BUILD_FAILURE"
        assert fail_event["data"]["status"] == "failed"

        # Receive SECURITY_ALERT broadcast
        sec_event = ws.receive_json()
        assert sec_event["type"] == "SECURITY_ALERT"
        assert sec_event["data"]["critical_count"] >= 1
        assert len(sec_event["data"]["findings"]) >= 1


def test_websocket_broadcasts_simulated_build_status():
    with client.websocket_connect("/api/v1/ws") as ws:
        # Discard handshake
        _ = ws.receive_json()

        # Fire failing build status
        payload = {
            "repository": "Ishan5497/Autonomous-DevOps-CI-CD-Pipeline-Health-Dashboard",
            "pipeline_id": "ws-pipe-555",
            "branch": "main",
            "commit_sha": "5555555555",
            "commit_message": "test: failing test suite",
            "author": "runner",
            "status": "failed",
            "stage": "test",
            "duration_seconds": 18.2,
            "failure_reason": "Unit tests failed: 3 assertions broken",
        }
        res = client.post("/api/v1/webhooks/simulate/build-status", json=payload)
        assert res.status_code == 200

        # Receive BUILD_FAILURE broadcast
        event = ws.receive_json()
        assert event["type"] == "BUILD_FAILURE"
        assert event["data"]["pipeline_id"] == "ws-pipe-555"
        assert event["data"]["failure_reason"] == "Unit tests failed: 3 assertions broken"

