import pytest

from power_quality import DisturbanceType, PowerQualityAnalyzer, SignalSimulator


@pytest.fixture
def analyzer() -> PowerQualityAnalyzer:
    return PowerQualityAnalyzer()


@pytest.mark.parametrize(
    ("disturbance", "expected"),
    [
        (DisturbanceType.NOMINAL, DisturbanceType.NOMINAL),
        (DisturbanceType.SAG, DisturbanceType.SAG),
        (DisturbanceType.SWELL, DisturbanceType.SWELL),
        (DisturbanceType.INTERRUPTION, DisturbanceType.INTERRUPTION),
        (DisturbanceType.HARMONIC_DISTORTION, DisturbanceType.HARMONIC_DISTORTION),
        (DisturbanceType.PHASE_UNBALANCE, DisturbanceType.PHASE_UNBALANCE),
    ],
)
def test_primary_class(analyzer, disturbance, expected):
    result = analyzer.analyze(SignalSimulator(seed=7).generate(disturbance))
    assert result.primary_class == expected


def test_nominal_metrics_are_close_to_reference(analyzer):
    result = analyzer.analyze(SignalSimulator(seed=1).generate())
    assert result.phase_a.rms_pu == pytest.approx(1.0, abs=0.01)
    assert result.phase_b.rms_pu == pytest.approx(1.0, abs=0.01)
    assert result.phase_c.rms_pu == pytest.approx(1.0, abs=0.01)
    assert result.voltage_unbalance_percent < 0.2


def test_harmonic_event_exposes_thd_evidence(analyzer):
    result = analyzer.analyze(
        SignalSimulator(seed=2).generate(DisturbanceType.HARMONIC_DISTORTION)
    )
    assert result.phase_a.thd_percent > 5.0
    assert DisturbanceType.HARMONIC_DISTORTION in {
        item.disturbance for item in result.detections
    }


def test_unbalance_is_detected(analyzer):
    result = analyzer.analyze(SignalSimulator(seed=3).generate(DisturbanceType.PHASE_UNBALANCE))
    assert result.voltage_unbalance_percent > 2.0
    assert DisturbanceType.PHASE_UNBALANCE in {item.disturbance for item in result.detections}


def test_simulator_is_reproducible():
    first = SignalSimulator(seed=99).generate()
    second = SignalSimulator(seed=99).generate()
    assert first.voltage_a == second.voltage_a
