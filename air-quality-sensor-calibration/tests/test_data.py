import pandas as pd
import pytest

from air_sensor.data import chronological_split


def test_split_is_ordered_and_disjoint() -> None:
    features = pd.DataFrame({"x": range(20)})
    target = pd.Series(range(20))
    split = chronological_split(features, target)
    assert split["train"][0]["x"].tolist() == list(range(16))
    assert split["calibration"][0]["x"].tolist() == [16, 17]
    assert split["test"][0]["x"].tolist() == [18, 19]


def test_split_rejects_invalid_fractions() -> None:
    with pytest.raises(ValueError):
        chronological_split(pd.DataFrame({"x": [1]}), pd.Series([1]), 0.9, 0.2)
