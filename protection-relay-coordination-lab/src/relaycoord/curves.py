"""IEC 60255 inverse-time curve equations used by the study engine."""

from math import isfinite

from .models import CurveType

CURVE_CONSTANTS: dict[CurveType, tuple[float, float]] = {
    CurveType.STANDARD_INVERSE: (0.14, 0.02),
    CurveType.VERY_INVERSE: (13.5, 1.0),
    CurveType.EXTREMELY_INVERSE: (80.0, 2.0),
}


def operating_time_s(
    current_a: float,
    pickup_a: float,
    time_multiplier: float,
    curve: CurveType,
) -> float | None:
    """Return theoretical operating time, or None when pickup is not reached."""
    multiple = current_a / pickup_a
    if multiple <= 1.0:
        return None
    coefficient, exponent = CURVE_CONSTANTS[curve]
    operating_time = time_multiplier * coefficient / (multiple**exponent - 1.0)
    if not isfinite(operating_time) or operating_time <= 0:
        raise ValueError("Calculated operating time is not finite and positive")
    return operating_time
