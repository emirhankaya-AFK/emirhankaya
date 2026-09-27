from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

DATA_URL = "https://archive.ics.uci.edu/static/public/360/air+quality.zip"
SENSOR_COLUMNS = [
    "PT08.S1(CO)",
    "PT08.S2(NMHC)",
    "PT08.S3(NOx)",
    "PT08.S4(NO2)",
    "PT08.S5(O3)",
    "T",
    "RH",
    "AH",
]
TARGET = "NO2(GT)"


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(data_dir: Path) -> dict[str, str]:
    data_dir.mkdir(parents=True, exist_ok=True)
    archive = data_dir / "air-quality.zip"
    raw = data_dir / "raw"
    if not archive.exists():
        urllib.request.urlretrieve(DATA_URL, archive)
    raw.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(raw)
    manifest = {"source": DATA_URL, "sha256": file_sha256(archive)}
    (data_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_dataset(data_dir: Path) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    csv_path = data_dir / "raw" / "AirQualityUCI.csv"
    if not csv_path.exists():
        download(data_dir)
    frame = pd.read_csv(csv_path, sep=";", decimal=",")
    frame = frame.dropna(axis=1, how="all").dropna(subset=["Date", "Time"])
    timestamps = pd.to_datetime(
        frame["Date"] + " " + frame["Time"], format="%d/%m/%Y %H.%M.%S"
    )
    numeric = frame[SENSOR_COLUMNS + [TARGET]].replace(-200, np.nan)
    valid = numeric[TARGET].notna()
    features = numeric.loc[valid, SENSOR_COLUMNS].copy()
    time = timestamps.loc[valid]
    features["hour_sin"] = np.sin(2 * np.pi * time.dt.hour / 24)
    features["hour_cos"] = np.cos(2 * np.pi * time.dt.hour / 24)
    features["day_sin"] = np.sin(2 * np.pi * time.dt.dayofyear / 365.25)
    features["day_cos"] = np.cos(2 * np.pi * time.dt.dayofyear / 365.25)
    return features.reset_index(drop=True), numeric.loc[valid, TARGET].reset_index(drop=True), time.reset_index(drop=True)


def chronological_split(
    features: pd.DataFrame, target: pd.Series, train_fraction: float = 0.80, calibration_fraction: float = 0.10
) -> dict[str, tuple[pd.DataFrame, pd.Series]]:
    if train_fraction <= 0 or calibration_fraction <= 0 or train_fraction + calibration_fraction >= 1:
        raise ValueError("Fractions must be positive and leave a test partition")
    train_end = int(len(features) * train_fraction)
    calibration_end = int(len(features) * (train_fraction + calibration_fraction))
    return {
        "train": (features.iloc[:train_end], target.iloc[:train_end]),
        "calibration": (features.iloc[train_end:calibration_end], target.iloc[train_end:calibration_end]),
        "test": (features.iloc[calibration_end:], target.iloc[calibration_end:]),
    }
