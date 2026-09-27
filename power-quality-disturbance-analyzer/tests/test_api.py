"""API smoke tests."""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_demo_classification() -> None:
    response = client.get("/demo/voltage_sag")
    assert response.status_code == 200
    assert response.json()["primary_class"] == "voltage_sag"


def test_unknown_demo_returns_validation_error() -> None:
    response = client.get("/demo/not-a-disturbance")
    assert response.status_code == 422


def test_dashboard_is_served() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Power Quality Disturbance Analyzer" in response.text
