import numpy as np
import pandas as pd
import pytest

from air_sensor.modeling import conformal_radius, population_stability_index


def test_conformal_radius_uses_absolute_residuals() -> None:
    radius = conformal_radius(np.array([1, 2, 3, 4]), np.array([1, 1, 3, 2]), 0.75)
    assert radius == 2


def test_conformal_radius_rejects_invalid_coverage() -> None:
    with pytest.raises(ValueError):
        conformal_radius(np.array([1]), np.array([1]), 1.0)


def test_psi_is_zero_for_identical_samples() -> None:
    sample = pd.Series(np.arange(100, dtype=float))
    assert population_stability_index(sample, sample) == pytest.approx(0.0)

