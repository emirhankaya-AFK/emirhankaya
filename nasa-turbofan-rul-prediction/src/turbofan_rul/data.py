"""C-MAPSS text parsing and leakage-safe target construction."""

from pathlib import Path

import numpy as np
import pandas as pd

COLUMNS = [
    "engine_id",
    "cycle",
    "setting_1",
    "setting_2",
    "setting_3",
    *[f"sensor_{index}" for index in range(1, 22)],
]

SENSORS = [
    "sensor_2",
    "sensor_3",
    "sensor_4",
    "sensor_7",
    "sensor_8",
    "sensor_9",
    "sensor_11",
    "sensor_12",
    "sensor_13",
    "sensor_14",
    "sensor_15",
    "sensor_17",
    "sensor_20",
    "sensor_21",
]


def read_trajectory(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, sep=r"\s+", header=None, names=COLUMNS)
    if frame.empty or frame.isna().any().any():
        raise ValueError(f"Invalid C-MAPSS trajectory file: {path}")
    frame["engine_id"] = frame["engine_id"].astype(int)
    frame["cycle"] = frame["cycle"].astype(int)
    return frame


def add_training_rul(frame: pd.DataFrame, cap: int = 125) -> pd.DataFrame:
    result = frame.copy()
    maximum_cycle = result.groupby("engine_id")["cycle"].transform("max")
    result["rul"] = np.minimum(maximum_cycle - result["cycle"], cap)
    return result


def read_test_targets(path: Path) -> np.ndarray:
    values = pd.read_csv(path, sep=r"\s+", header=None).iloc[:, 0].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Invalid test RUL targets")
    return values
