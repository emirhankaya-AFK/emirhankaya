import numpy as np

from semiconductor_yield.metrics import classification_metrics


def test_classification_metrics_confusion_counts_and_cost() -> None:
    metrics = classification_metrics(
        np.array([0, 0, 1, 1]), np.array([0.1, 0.7, 0.4, 0.9]), threshold=0.5
    )
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["weighted_cost"] == 11

