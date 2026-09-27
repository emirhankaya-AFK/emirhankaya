from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def select_train_columns(features: pd.DataFrame, max_missing: float = 0.60) -> list[str]:
    """Choose columns using training data only."""
    missing = features.isna().mean()
    varying = features.nunique(dropna=True) > 1
    return features.columns[(missing <= max_missing) & varying].tolist()


def build_logistic_model(random_state: int = 42) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("variance", VarianceThreshold()),
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    C=0.05,
                    class_weight="balanced",
                    max_iter=3000,
                    random_state=random_state,
                ),
            ),
        ]
    )


def positive_probability(model: BaseEstimator, features: pd.DataFrame) -> np.ndarray:
    return np.asarray(model.predict_proba(features))[:, 1]


def choose_cost_threshold(
    y_true: pd.Series | np.ndarray,
    probability: np.ndarray,
    false_negative_cost: float = 10.0,
    false_positive_cost: float = 1.0,
) -> tuple[float, float]:
    y = np.asarray(y_true)
    candidates = np.unique(np.concatenate(([0.0], probability, [1.0])))
    best_threshold, best_cost = 0.5, float("inf")
    for threshold in candidates:
        prediction = probability >= threshold
        false_negatives = int(((y == 1) & ~prediction).sum())
        false_positives = int(((y == 0) & prediction).sum())
        cost = false_negative_cost * false_negatives + false_positive_cost * false_positives
        if cost < best_cost or (cost == best_cost and abs(threshold - 0.5) < abs(best_threshold - 0.5)):
            best_threshold, best_cost = float(threshold), float(cost)
    return best_threshold, best_cost


def choose_recall_threshold(
    y_true: pd.Series | np.ndarray,
    probability: np.ndarray,
    minimum_recall: float = 0.50,
) -> float:
    """Select the highest validation-only threshold that meets a recall floor."""
    if not 0 < minimum_recall <= 1:
        raise ValueError("minimum_recall must be in (0, 1]")
    candidates = np.unique(probability)
    feasible = [
        threshold
        for threshold in candidates
        if recall_score(y_true, probability >= threshold, zero_division=0) >= minimum_recall
    ]
    if not feasible:
        return 0.0
    return float(max(feasible))
