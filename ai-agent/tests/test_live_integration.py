import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "railway"


def test_health_ready_endpoint():
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_suggestions_endpoint():
    response = client.get("/suggestions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_automation_detect_endpoint():
    response = client.get("/api/v1/automation/detect")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "summary" in data
    assert "candidates" in data


def test_ask_endpoint_factual_query():
    response = client.post("/ask", json={"question": "How many total employees are in the system?"})
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "session_id" in data
    assert isinstance(data["tool_calls"], list)
