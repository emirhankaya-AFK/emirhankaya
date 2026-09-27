import pandas as pd
import pytest

from semiconductor_yield.data import chronological_split


def test_chronological_split_preserves_time_order() -> None:
    features = pd.DataFrame({"value": [30, 10, 40, 20, 50]})
    target = pd.Series([0, 0, 1, 0, 1])
    timestamps = pd.to_datetime(
        pd.Series(["2024-01-03", "2024-01-01", "2024-01-04", "2024-01-02", "2024-01-05"])
    )
    split = chronological_split(features, target, timestamps, 0.4, 0.2)
    assert split["train"][0]["value"].tolist() == [10, 20]
    assert split["validation"][0]["value"].tolist() == [30]
    assert split["test"][0]["value"].tolist() == [40, 50]


def test_chronological_split_rejects_invalid_fractions() -> None:
    frame = pd.DataFrame({"value": [1, 2]})
    target = pd.Series([0, 1])
    timestamps = pd.to_datetime(pd.Series(["2024-01-01", "2024-01-02"]))
    with pytest.raises(ValueError):
        chronological_split(frame, target, timestamps, 0.8, 0.3)

