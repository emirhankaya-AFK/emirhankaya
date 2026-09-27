from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

DATA_URL = "https://archive.ics.uci.edu/static/public/179/secom.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_dataset(data_dir: Path) -> dict[str, object]:
    data_dir.mkdir(parents=True, exist_ok=True)
    archive = data_dir / "secom.zip"
    raw_dir = data_dir / "raw"
    if not archive.exists():
        urllib.request.urlretrieve(DATA_URL, archive)
    raw_dir.mkdir(exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(raw_dir)
    manifest = {
        "source": DATA_URL,
        "sha256": sha256(archive),
        "files": sorted(path.name for path in raw_dir.iterdir() if path.is_file()),
    }
    (data_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def load_secom(data_dir: Path) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    raw_dir = data_dir / "raw"
    feature_path = raw_dir / "secom.data"
    label_path = raw_dir / "secom_labels.data"
    if not feature_path.exists() or not label_path.exists():
        download_dataset(data_dir)
    features = pd.read_csv(feature_path, sep=r"\s+", header=None)
    features.columns = [f"sensor_{column:03d}" for column in range(features.shape[1])]
    labels = pd.read_csv(label_path, sep=r"\s+", header=None, names=["label", "date", "time"])
    target = labels["label"].map({-1: 0, 1: 1}).astype(int).rename("failed")
    timestamps = pd.to_datetime(labels["date"] + " " + labels["time"], format="%d/%m/%Y %H:%M:%S")
    return features, target, timestamps


def chronological_split(
    features: pd.DataFrame,
    target: pd.Series,
    timestamps: pd.Series,
    train_fraction: float = 0.60,
    validation_fraction: float = 0.20,
) -> dict[str, tuple[pd.DataFrame, pd.Series]]:
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1:
        raise ValueError("Split fractions must be between zero and one")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("Train and validation fractions must leave a test set")
    order = timestamps.sort_values(kind="stable").index
    x_ordered = features.loc[order].reset_index(drop=True)
    y_ordered = target.loc[order].reset_index(drop=True)
    train_end = int(len(order) * train_fraction)
    validation_end = int(len(order) * (train_fraction + validation_fraction))
    return {
        "train": (x_ordered.iloc[:train_end], y_ordered.iloc[:train_end]),
        "validation": (x_ordered.iloc[train_end:validation_end], y_ordered.iloc[train_end:validation_end]),
        "test": (x_ordered.iloc[validation_end:], y_ordered.iloc[validation_end:]),
    }

