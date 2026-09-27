import numpy as np
import pandas as pd

from semiconductor_yield.modeling import (
    choose_cost_threshold,
    choose_recall_threshold,
    select_train_columns,
)


def test_train_column_selection_drops_constant_and_sparse_columns() -> None:
    frame = pd.DataFrame(
        {
            "useful": [1.0, 2.0, 3.0, 4.0],
            "constant": [7.0, 7.0, 7.0, 7.0],
            "sparse": [np.nan, np.nan, np.nan, 1.0],
        }
    )
    assert select_train_columns(frame, max_missing=0.5) == ["useful"]


def test_cost_threshold_penalizes_missed_failures() -> None:
    y = np.array([0, 0, 0, 1])
    probability = np.array([0.1, 0.2, 0.3, 0.4])
    threshold, cost = choose_cost_threshold(y, probability, 10, 1)
    assert threshold == 0.4
    assert cost == 0


def test_recall_threshold_uses_highest_feasible_cutoff() -> None:
    y = np.array([0, 0, 1, 1])
    probability = np.array([0.1, 0.6, 0.4, 0.8])
    assert choose_recall_threshold(y, probability, minimum_recall=0.5) == 0.8
