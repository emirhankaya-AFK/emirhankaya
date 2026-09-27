from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(
    y_true: np.ndarray,
    probability: np.ndarray,
    threshold: float,
    false_negative_cost: float = 10.0,
    false_positive_cost: float = 1.0,
) -> dict[str, float | int]:
    y = np.asarray(y_true)
    prediction = probability >= threshold
    tn, fp, fn, tp = confusion_matrix(y, prediction, labels=[0, 1]).ravel()
    return {
        "samples": len(y),
        "failures": int(y.sum()),
        "threshold": float(threshold),
        "pr_auc": float(average_precision_score(y, probability)),
        "roc_auc": float(roc_auc_score(y, probability)),
        "balanced_accuracy": float(balanced_accuracy_score(y, prediction)),
        "recall": float(recall_score(y, prediction, zero_division=0)),
        "specificity": float(tn / (tn + fp)),
        "precision": float(precision_score(y, prediction, zero_division=0)),
        "f1": float(f1_score(y, prediction, zero_division=0)),
        "brier": float(brier_score_loss(y, probability)),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp),
        "true_negatives": int(tn),
        "weighted_cost": float(false_negative_cost * fn + false_positive_cost * fp),
    }


def bootstrap_interval(
    y_true: np.ndarray,
    probability: np.ndarray,
    metric: str,
    n_bootstrap: int = 2000,
    random_state: int = 42,
) -> tuple[float, float]:
    y = np.asarray(y_true)
    rng = np.random.default_rng(random_state)
    values: list[float] = []
    scorer = average_precision_score if metric == "pr_auc" else roc_auc_score
    for _ in range(n_bootstrap):
        indices = rng.integers(0, len(y), len(y))
        if np.unique(y[indices]).size < 2:
            continue
        values.append(float(scorer(y[indices], probability[indices])))
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))
