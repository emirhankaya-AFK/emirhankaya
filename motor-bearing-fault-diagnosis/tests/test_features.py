import numpy as np

from bearing_fault.features import extract_features, feature_names


def test_feature_vector_is_finite_and_named():
    time = np.arange(2048) / 12_000
    signal = np.sin(2 * np.pi * 1000 * time)
    features = extract_features(signal)
    assert len(features) == len(feature_names())
    assert np.isfinite(features).all()


def test_dominant_frequency_finds_known_tone():
    time = np.arange(2048) / 12_000
    signal = np.sin(2 * np.pi * 750 * time)
    values = dict(zip(feature_names(), extract_features(signal), strict=True))
    assert abs(values["dominant_frequency_hz"] - 750) < 6
