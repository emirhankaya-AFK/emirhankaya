"""CWRU bearing fault diagnosis utilities."""

from .data import load_dataset, load_drive_end_signal, split_windows
from .features import extract_feature_matrix, extract_features, feature_names
from .manifest import LABELS, RECORDINGS, SAMPLE_RATE_HZ
from .metrics import add_gaussian_noise_at_snr, expected_calibration_error, multiclass_brier_score

__all__ = [
    "LABELS",
    "RECORDINGS",
    "SAMPLE_RATE_HZ",
    "add_gaussian_noise_at_snr",
    "expected_calibration_error",
    "extract_feature_matrix",
    "extract_features",
    "feature_names",
    "load_dataset",
    "load_drive_end_signal",
    "multiclass_brier_score",
    "split_windows",
]
