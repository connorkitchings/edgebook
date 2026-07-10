"""
Test cases for the API endpoints.
"""

from fastapi.testclient import TestClient

from vibe_coding.api.main import app

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_predict_endpoint():
    response = client.post("/predict/", json={"data": [1.0, 2.0, 3.0]})
    assert response.status_code == 200
    assert "prediction" in response.json()
    assert response.json()["prediction"] == 6.0  # Based on the placeholder sum logic
