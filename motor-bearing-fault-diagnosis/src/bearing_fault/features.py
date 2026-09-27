"""Time, frequency, and wavelet feature extraction."""

import numpy as np
import pywt
from scipy.stats import kurtosis, skew

from .manifest import SAMPLE_RATE_HZ


def feature_names(wavelet_level: int = 4) -> list[str]:
    return [
        "rms",
        "std",
        "skewness",
        "kurtosis",
        "peak",
        "crest_factor",
        "impulse_factor",
        "shape_factor",
        "spectral_centroid_hz",
        "spectral_entropy",
        "dominant_frequency_hz",
        *[f"band_energy_{index}" for index in range(6)],
        *[f"wavelet_energy_{index}" for index in range(wavelet_level + 1)],
    ]


def extract_features(window: np.ndarray, sample_rate: int = SAMPLE_RATE_HZ) -> np.ndarray:
    values = np.asarray(window, dtype=np.float64)
    centered = values - values.mean()
    absolute = np.abs(centered)
    rms = np.sqrt(np.mean(centered**2))
    mean_absolute = absolute.mean()
    peak = absolute.max()

    spectrum = np.abs(np.fft.rfft(centered * np.hanning(len(centered)))) ** 2
    frequencies = np.fft.rfftfreq(len(centered), 1 / sample_rate)
    spectrum_sum = spectrum.sum() + 1e-12
    probabilities = spectrum / spectrum_sum
    centroid = float(np.sum(frequencies * probabilities))
    entropy = float(-np.sum(probabilities * np.log2(probabilities + 1e-12)))
    dominant = float(frequencies[int(np.argmax(spectrum[1:])) + 1])
    band_edges = np.linspace(0, sample_rate / 2, 7)
    band_energies = [
        float(spectrum[(frequencies >= left) & (frequencies < right)].sum() / spectrum_sum)
        for left, right in zip(band_edges[:-1], band_edges[1:], strict=True)
    ]

    coefficients = pywt.wavedec(centered, "db4", level=4)
    wavelet_energy = np.asarray([np.sum(coefficient**2) for coefficient in coefficients])
    wavelet_energy = (wavelet_energy / (wavelet_energy.sum() + 1e-12)).tolist()

    return np.asarray(
        [
            rms,
            centered.std(),
            skew(centered, bias=False),
            kurtosis(centered, fisher=True, bias=False),
            peak,
            peak / (rms + 1e-12),
            peak / (mean_absolute + 1e-12),
            rms / (mean_absolute + 1e-12),
            centroid,
            entropy,
            dominant,
            *band_energies,
            *wavelet_energy,
        ],
        dtype=np.float64,
    )


def extract_feature_matrix(windows: np.ndarray) -> np.ndarray:
    return np.stack([extract_features(window) for window in windows])
