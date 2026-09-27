import numpy as np

from src.train import business_cost, select_threshold


def test_business_cost_penalizes_missed_fraud_more():
    y = np.array([0, 0, 1, 1])
    assert business_cost(y, np.array([0, 1, 1, 1])) == 5
    assert business_cost(y, np.array([0, 0, 0, 1])) == 250


def test_threshold_selection_returns_valid_value():
    threshold, cost = select_threshold(np.array([0, 0, 1, 1]), np.array([0.1, 0.2, 0.7, 0.9]))
    assert 0 < threshold < 1
    assert cost == 0

