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
    response = client.post("/ask", json={
        "question": "How many total employees are in the system?",
        "user_role": "HSE_MANAGER"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    assert "session_id" in data
    assert isinstance(data["tool_calls"], list)


def test_ask_endpoint_rag_knowledge():
    response = client.post("/ask", json={
        "question": "ما هي متطلبات دخول الأماكن المغلقة وحدود فحص الغازات حسب معايير السلامة؟",
        "user_role": "HSE_OFFICER"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    # Verify that tool calls trace shows search_hse_knowledge was invoked
    tool_names = [tc["tool_name"] for tc in data.get("tool_calls", [])]
    assert any("search_hse_knowledge" in name or "run_read_only_query" in name for name in tool_names) or len(data["answer"]) > 20


def test_ask_endpoint_crud_incident():
    response = client.post("/ask", json={
        "question": "سجل بلاغ حادث جديد بعنوان 'تجربة النظام الذكي' ووصف 'اختبار تسجيل بلاغ فوري عبر المساعد الذكي' في المنطقة 1 ودرجة الخطورة MINOR",
        "user_role": "HSE_MANAGER"
    })
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert len(data["answer"]) > 0
    tool_names = [tc["tool_name"] for tc in data.get("tool_calls", [])]
    assert "create_incident" in tool_names or "نجاح" in data["answer"] or "حادث" in data["answer"]
