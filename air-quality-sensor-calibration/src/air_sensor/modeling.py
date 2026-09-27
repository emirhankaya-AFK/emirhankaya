from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def build_model() -> TransformedTargetRegressor:
    regressor = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
            ("model", HistGradientBoostingRegressor(max_iter=350, learning_rate=0.05, max_leaf_nodes=20, l2_regularization=2.0, random_state=42)),
        ]
    )
    return TransformedTargetRegressor(regressor=regressor, transformer=StandardScaler())


def conformal_radius(actual: np.ndarray, prediction: np.ndarray, coverage: float = 0.90) -> float:
    if not 0 < coverage < 1:
        raise ValueError("coverage must be between zero and one")
    residuals = np.abs(np.asarray(actual) - np.asarray(prediction))
    level = min(1.0, np.ceil((len(residuals) + 1) * coverage) / len(residuals))
    return float(np.quantile(residuals, level, method="higher"))


def population_stability_index(reference: pd.Series, current: pd.Series, bins: int = 10) -> float:
    reference = reference.dropna().to_numpy()
    current = current.dropna().to_numpy()
    edges = np.unique(np.quantile(reference, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    ref_hist = np.histogram(reference, bins=edges)[0] / len(reference)
    cur_hist = np.histogram(current, bins=edges)[0] / len(current)
    ref_hist = np.clip(ref_hist, 1e-6, None)
    cur_hist = np.clip(cur_hist, 1e-6, None)
    return float(np.sum((cur_hist - ref_hist) * np.log(cur_hist / ref_hist)))

