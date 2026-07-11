"""Test cases for Edgebook API endpoints."""

from fastapi.testclient import TestClient

from edgebook.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check status and service connectivity."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["services"]["api"] == "ok"
    assert data["services"]["database"] == "ok"
