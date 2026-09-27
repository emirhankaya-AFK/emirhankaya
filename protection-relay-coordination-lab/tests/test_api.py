from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_dashboard_and_health():
    assert client.get("/").status_code == 200
    assert client.get("/health").json()["status"] == "ok"


def test_preset_contract():
    response = client.get("/presets/coordinated")
    assert response.status_code == 200
    assert response.json()["result"]["all_coordinated"] is True


def test_invalid_custom_study_is_rejected():
    response = client.post("/analyze", json={"relays": []})
    assert response.status_code == 422
