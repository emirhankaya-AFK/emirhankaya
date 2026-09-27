"""Causal rolling features computed separately inside each engine trajectory."""

import numpy as np
import pandas as pd

from .data import SENSORS


def _slope(values: np.ndarray) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    return float(np.polyfit(x, values, 1)[0])


def build_features(frame: pd.DataFrame, windows: tuple[int, ...] = (5, 10)) -> pd.DataFrame:
    result = frame[["engine_id", "cycle", "setting_1", "setting_2", "setting_3", *SENSORS]].copy()
    grouped = frame.groupby("engine_id", sort=False)
    for window in windows:
        for sensor in SENSORS:
            rolling = grouped[sensor].rolling(window, min_periods=1)
            result[f"{sensor}_mean_{window}"] = rolling.mean().reset_index(level=0, drop=True)
            result[f"{sensor}_std_{window}"] = (
                rolling.std().reset_index(level=0, drop=True).fillna(0.0)
            )
            result[f"{sensor}_slope_{window}"] = grouped[sensor].transform(
                lambda values, size=window: values.rolling(size, min_periods=2).apply(
                    _slope, raw=True
                )
            ).fillna(0.0)
    return result.drop(columns="engine_id")


def last_cycle_rows(frame: pd.DataFrame) -> pd.DataFrame:
    indices = frame.groupby("engine_id")["cycle"].idxmax()
    return frame.loc[indices].sort_values("engine_id")
