"""MATLAB loading and non-overlapping window generation."""

from pathlib import Path

import numpy as np
from scipy.io import loadmat

from .manifest import RECORDINGS, Recording


def load_drive_end_signal(path: Path) -> np.ndarray:
    content = loadmat(path)
    expected_key = f"X{int(path.stem):03d}_DE_time"
    if expected_key not in content:
        candidates = [key for key in content if key.endswith("DE_time")]
        raise ValueError(f"Expected {expected_key} in {path.name}, found {candidates}")
    signal = np.asarray(content[expected_key], dtype=np.float64).reshape(-1)
    if signal.size < 4096 or not np.isfinite(signal).all():
        raise ValueError(f"Invalid vibration signal in {path.name}")
    return signal


def split_windows(signal: np.ndarray, window_size: int = 2048, stride: int = 2048) -> np.ndarray:
    if window_size <= 0 or stride <= 0 or signal.size < window_size:
        raise ValueError("Signal and window parameters do not produce a complete window")
    starts = range(0, signal.size - window_size + 1, stride)
    return np.stack([signal[start : start + window_size] for start in starts])


def load_dataset(data_dir: Path, window_size: int = 2048) -> tuple[np.ndarray, ...]:
    windows: list[np.ndarray] = []
    labels: list[str] = []
    loads: list[int] = []
    recording_ids: list[int] = []
    for recording in RECORDINGS:
        signal = load_drive_end_signal(data_dir / f"{recording.file_id}.mat")
        chunks = split_windows(signal, window_size=window_size)
        windows.extend(chunks)
        labels.extend([recording.label] * len(chunks))
        loads.extend([recording.load_hp] * len(chunks))
        recording_ids.extend([recording.file_id] * len(chunks))
    return (
        np.asarray(windows),
        np.asarray(labels),
        np.asarray(loads),
        np.asarray(recording_ids),
    )


def recording_for(file_id: int) -> Recording:
    return next(recording for recording in RECORDINGS if recording.file_id == file_id)
