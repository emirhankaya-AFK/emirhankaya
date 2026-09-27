import pytest

from relaycoord import CurveType, operating_time_s


@pytest.mark.parametrize(
    ("curve", "expected"),
    [
        (CurveType.STANDARD_INVERSE, 0.5941),
        (CurveType.VERY_INVERSE, 0.3),
        (CurveType.EXTREMELY_INVERSE, 0.1616),
    ],
)
def test_known_ten_times_pickup_values(curve, expected):
    assert operating_time_s(1000, 100, 0.2, curve) == pytest.approx(expected, rel=0.01)


def test_no_operation_at_or_below_pickup():
    assert operating_time_s(100, 100, 0.2, CurveType.STANDARD_INVERSE) is None
    assert operating_time_s(90, 100, 0.2, CurveType.STANDARD_INVERSE) is None
