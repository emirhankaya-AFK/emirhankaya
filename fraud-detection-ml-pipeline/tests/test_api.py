from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def test_health():
    assert client.get("/health").json()["status"] == "healthy"


def test_prediction_contract():
    payload = {
        "amount": 900,
        "hour": 2,
        "account_age_days": 100,
        "distance_from_home_km": 180,
        "transactions_last_24h": 12,
        "merchant_risk_score": 0.8,
        "is_foreign": 1,
        "is_card_present": 0,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert 0 <= body["fraud_probability"] <= 1
    assert body["decision"] in {"approve", "review"}
    assert len(body["top_risk_signals"]) == 3

