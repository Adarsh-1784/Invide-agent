import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "EcoNITH Backend" in data["service"]

def test_get_locations():
    response = client.get("/api/locations")
    assert response.status_code == 200
    data = response.json()
    assert "locations" in data
    assert len(data["locations"]) > 0

def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_reports" in data
    assert "waste_breakdown" in data
    assert isinstance(data["total_reports"], int)

def test_get_reports():
    response = client.get("/api/reports?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data
    assert "total" in data
    assert isinstance(data["reports"], list)

def test_get_hotspots():
    response = client.get("/api/hotspots")
    assert response.status_code == 200
    data = response.json()
    assert "hotspots" in data
    assert isinstance(data["hotspots"], list)

def test_agent_chat_demo_mode():
    # Setup test message
    payload = {
        "message": "Hello, agent!",
        "history": []
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "mode" in data
    # Should contain a response string
    assert isinstance(data["response"], str)
