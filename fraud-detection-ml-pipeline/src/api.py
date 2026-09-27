"""FastAPI scoring service and lightweight portfolio dashboard."""

from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from src.data import FEATURES

ROOT = Path(__file__).resolve().parents[1]


class Transaction(BaseModel):
    amount: float = Field(ge=0, le=100_000)
    hour: int = Field(ge=0, le=23)
    account_age_days: int = Field(ge=0, le=50_000)
    distance_from_home_km: float = Field(ge=0, le=20_000)
    transactions_last_24h: int = Field(ge=0, le=1_000)
    merchant_risk_score: float = Field(ge=0, le=1)
    is_foreign: int = Field(ge=0, le=1)
    is_card_present: int = Field(ge=0, le=1)


@lru_cache
def load_bundle() -> dict:
    path = ROOT / "artifacts" / "model.joblib"
    if not path.exists():
        from src.train import run_training

        run_training()
    return joblib.load(path)


def explain(transaction: Transaction) -> list[dict]:
    values = transaction.model_dump()
    signals = [
        ("high transaction amount", min(values["amount"] / 1_000, 1)),
        ("merchant risk", values["merchant_risk_score"]),
        ("distance from home", min(values["distance_from_home_km"] / 200, 1)),
        ("unusual transaction velocity", min(values["transactions_last_24h"] / 15, 1)),
        ("foreign transaction", values["is_foreign"]),
        ("card not present", 1 - values["is_card_present"]),
        ("late-night activity", int(values["hour"] <= 5 or values["hour"] >= 23) * 0.7),
    ]
    return [
        {"factor": label, "risk_contribution": round(float(score), 2)}
        for label, score in sorted(signals, key=lambda item: item[1], reverse=True)[:3]
    ]


app = FastAPI(title="Fraud Detection ML Pipeline", version="1.0.0")


@app.get("/health")
def health() -> dict:
    return {"status": "healthy", "model_loaded": True}


@app.post("/predict")
def predict(transaction: Transaction) -> dict:
    bundle = load_bundle()
    frame = pd.DataFrame([[getattr(transaction, name) for name in FEATURES]], columns=FEATURES)
    probability = float(bundle["model"].predict_proba(frame)[0, 1])
    return {
        "fraud_probability": round(probability, 4),
        "decision": "review" if probability >= bundle["threshold"] else "approve",
        "threshold": bundle["threshold"],
        "top_risk_signals": explain(transaction),
        "disclaimer": "Decision support only; human review is required.",
    }


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return (ROOT / "src" / "dashboard.html").read_text(encoding="utf-8")

