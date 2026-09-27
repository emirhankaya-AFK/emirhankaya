"""Reliability and robustness metrics not provided by the basic classifier report."""

import numpy as np


def expected_calibration_error(
    probabilities: np.ndarray, targets: np.ndarray, bins: int = 10
) -> float:
    if probabilities.ndim != 2 or len(probabilities) != len(targets):
        raise ValueError("Probabilities and targets must describe the same samples")
    confidence = probabilities.max(axis=1)
    predictions = probabilities.argmax(axis=1)
    edges = np.linspace(0.0, 1.0, bins + 1)
    error = 0.0
    for index in range(bins):
        lower, upper = edges[index], edges[index + 1]
        mask = (confidence > lower) & (confidence <= upper)
        if mask.any():
            accuracy = np.mean(predictions[mask] == targets[mask])
            error += np.mean(mask) * abs(accuracy - np.mean(confidence[mask]))
    return float(error)


def multiclass_brier_score(probabilities: np.ndarray, targets: np.ndarray) -> float:
    if probabilities.ndim != 2 or len(probabilities) != len(targets):
        raise ValueError("Probabilities and targets must describe the same samples")
    one_hot = np.eye(probabilities.shape[1])[targets]
    return float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1)))


def add_gaussian_noise_at_snr(
    windows: np.ndarray, snr_db: float, seed: int = 42
) -> np.ndarray:
    values = np.asarray(windows, dtype=np.float64)
    generator = np.random.default_rng(seed)
    signal_power = np.mean(values**2, axis=1, keepdims=True)
    noise_power = signal_power / (10 ** (snr_db / 10))
    noise = generator.normal(size=values.shape) * np.sqrt(noise_power)
    return values + noise
