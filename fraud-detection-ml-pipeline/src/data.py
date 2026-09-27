"""Reproducible synthetic card-transaction data."""

from pathlib import Path

import numpy as np
import pandas as pd

FEATURES = [
    "amount",
    "hour",
    "account_age_days",
    "distance_from_home_km",
    "transactions_last_24h",
    "merchant_risk_score",
    "is_foreign",
    "is_card_present",
]


def generate_transactions(n_samples: int = 20_000, seed: int = 42) -> pd.DataFrame:
    """Create realistic-looking synthetic transactions without customer PII."""
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "amount": np.clip(rng.lognormal(4.2, 1.05, n_samples), 1, 10_000),
            "hour": rng.integers(0, 24, n_samples),
            "account_age_days": rng.integers(1, 3_650, n_samples),
            "distance_from_home_km": np.clip(rng.exponential(18, n_samples), 0, 500),
            "transactions_last_24h": np.clip(rng.poisson(3, n_samples), 0, 30),
            "merchant_risk_score": rng.beta(1.4, 7, n_samples),
            "is_foreign": rng.binomial(1, 0.07, n_samples),
            "is_card_present": rng.binomial(1, 0.72, n_samples),
        }
    )
    night = ((frame["hour"] <= 5) | (frame["hour"] >= 23)).astype(int)
    log_odds = (
        -7.8
        + 0.0055 * frame["amount"]
        + 0.010 * frame["distance_from_home_km"]
        + 0.22 * frame["transactions_last_24h"]
        + 4.2 * frame["merchant_risk_score"]
        + 1.1 * frame["is_foreign"]
        + 0.7 * (1 - frame["is_card_present"])
        + 0.65 * night
        - 0.0002 * frame["account_age_days"]
    )
    probability = 1 / (1 + np.exp(-np.clip(log_odds, -20, 20)))
    frame["is_fraud"] = rng.binomial(1, probability)
    return frame


def save_dataset(path: Path, n_samples: int = 20_000, seed: int = 42) -> pd.DataFrame:
    frame = generate_transactions(n_samples=n_samples, seed=seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return frame

