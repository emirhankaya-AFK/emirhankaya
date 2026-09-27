import numpy as np

from turbofan_rul.metrics import nasa_score, regression_metrics


def test_late_predictions_receive_larger_penalty():
    actual = np.array([50.0])
    assert nasa_score(actual, np.array([60.0])) > nasa_score(actual, np.array([40.0]))


def test_regression_metrics_known_example():
    result = regression_metrics(np.array([10.0, 20.0]), np.array([12.0, 18.0]))
    assert result["mae"] == 2
    assert result["rmse"] == 2
    assert result["late_prediction_rate"] == 0.5
