import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models.database import init_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield


def test_pipeline_health_endpoint():
    response = client.get("/api/v1/pipeline/health")
    assert response.status_code == 200
    data = response.json()
    assert "health_grade" in data
    assert "success_rate_percent" in data
    assert "mttr_seconds" in data
    assert "recommendations" in data


def test_dashboard_summary_endpoint():
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "health" in data
    assert "recent_runs" in data
    assert "recent_pull_requests" in data
    assert "recent_findings" in data
    assert "system_status" in data


def test_dashboard_ui_endpoint():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_seed_demo_data():
    response = client.post("/api/v1/dashboard/seed-demo-data")
    assert response.status_code == 200
    assert response.json()["status"] in ("success", "ok")
