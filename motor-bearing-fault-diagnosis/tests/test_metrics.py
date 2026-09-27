import numpy as np

from bearing_fault.metrics import (
    add_gaussian_noise_at_snr,
    expected_calibration_error,
    multiclass_brier_score,
)


def test_perfect_probabilities_have_zero_calibration_and_brier_error():
    probabilities = np.eye(3)
    targets = np.array([0, 1, 2])
    assert expected_calibration_error(probabilities, targets) == 0
    assert multiclass_brier_score(probabilities, targets) == 0


def test_noise_generator_is_reproducible_and_near_requested_snr():
    windows = np.ones((10, 4096))
    first = add_gaussian_noise_at_snr(windows, 10, seed=7)
    second = add_gaussian_noise_at_snr(windows, 10, seed=7)
    measured_snr = 10 * np.log10(np.mean(windows**2) / np.mean((first - windows) ** 2))
    assert np.array_equal(first, second)
    np.testing.assert_allclose(measured_snr, 10, atol=0.2)
