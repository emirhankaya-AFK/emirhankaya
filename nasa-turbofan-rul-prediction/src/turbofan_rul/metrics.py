"""RUL regression metrics including the PHM08 asymmetric penalty."""

import numpy as np


def nasa_score(actual: np.ndarray, predicted: np.ndarray) -> float:
    errors = np.asarray(predicted) - np.asarray(actual)
    penalties = np.where(errors < 0, np.exp(-errors / 13) - 1, np.exp(errors / 10) - 1)
    return float(np.sum(penalties))


def regression_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    errors = np.asarray(predicted) - np.asarray(actual)
    return {
        "mae": round(float(np.mean(np.abs(errors))), 4),
        "rmse": round(float(np.sqrt(np.mean(errors**2))), 4),
        "nasa_score": round(nasa_score(actual, predicted), 4),
        "late_prediction_rate": round(float(np.mean(errors > 0)), 4),
    }
