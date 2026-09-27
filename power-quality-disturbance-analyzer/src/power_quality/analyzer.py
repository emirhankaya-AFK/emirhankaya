"""Deterministic signal-processing pipeline for educational power-quality analysis."""

from __future__ import annotations

import numpy as np

from .models import AnalysisResult, Detection, DisturbanceType, PhaseMetrics, SignalWindow


class PowerQualityAnalyzer:
    """Detect disturbances using explicit, configurable prototype thresholds.

    The defaults are engineering-oriented demonstration values. They are not a
    declaration of IEC/IEEE compliance and must be calibrated for real hardware.
    """

    def __init__(
        self,
        interruption_pu: float = 0.10,
        sag_pu: float = 0.90,
        swell_pu: float = 1.10,
        thd_percent: float = 5.0,
        unbalance_percent: float = 2.0,
    ) -> None:
        self.thresholds = {
            "interruption_pu": interruption_pu,
            "sag_pu": sag_pu,
            "swell_pu": swell_pu,
            "thd_percent": thd_percent,
            "unbalance_percent": unbalance_percent,
        }

    @staticmethod
    def _rms(samples: np.ndarray) -> float:
        return float(np.sqrt(np.mean(np.square(samples))))

    @staticmethod
    def _fundamental_phasor(samples: np.ndarray, sample_rate: float, frequency: float) -> complex:
        n = len(samples)
        time = np.arange(n) / sample_rate
        basis = np.exp(-1j * 2 * np.pi * frequency * time)
        return complex((2.0 / n) * np.sum(samples * basis))

    @staticmethod
    def _thd(samples: np.ndarray, sample_rate: float, frequency: float) -> float:
        centered = samples - np.mean(samples)
        spectrum = np.abs(np.fft.rfft(centered)) * 2.0 / len(centered)
        frequencies = np.fft.rfftfreq(len(centered), d=1.0 / sample_rate)

        def amplitude(target: float) -> float:
            index = int(np.argmin(np.abs(frequencies - target)))
            return float(spectrum[index])

        fundamental = amplitude(frequency)
        if fundamental < 1e-9:
            return 0.0
        harmonics = [amplitude(frequency * order) for order in range(2, 11)]
        return float(np.sqrt(np.sum(np.square(harmonics))) / fundamental * 100.0)

    def analyze(self, window: SignalWindow) -> AnalysisResult:
        arrays = [
            np.asarray(window.voltage_a, dtype=float),
            np.asarray(window.voltage_b, dtype=float),
            np.asarray(window.voltage_c, dtype=float),
        ]
        rms_values = [self._rms(values) for values in arrays]
        rms_pu = [value / window.nominal_voltage_rms for value in rms_values]
        thd_values = [
            self._thd(values, window.sample_rate_hz, window.nominal_frequency_hz)
            for values in arrays
        ]

        phasors = [
            self._fundamental_phasor(
                values,
                window.sample_rate_hz,
                window.nominal_frequency_hz,
            )
            for values in arrays
        ]
        rotation = np.exp(1j * 2 * np.pi / 3)
        positive = (phasors[0] + rotation * phasors[1] + rotation**2 * phasors[2]) / 3
        negative = (phasors[0] + rotation**2 * phasors[1] + rotation * phasors[2]) / 3
        unbalance = abs(negative) / max(abs(positive), 1e-9) * 100.0

        detections: list[Detection] = []
        min_pu = min(rms_pu)
        max_pu = max(rms_pu)
        max_thd = max(thd_values)

        if min_pu < self.thresholds["interruption_pu"]:
            detections.append(
                Detection(
                    disturbance=DisturbanceType.INTERRUPTION,
                    severity="critical",
                    evidence=f"Minimum phase RMS is {min_pu:.3f} pu",
                )
            )
        elif min_pu < self.thresholds["sag_pu"]:
            detections.append(
                Detection(
                    disturbance=DisturbanceType.SAG,
                    severity="warning",
                    evidence=f"Minimum phase RMS is {min_pu:.3f} pu",
                )
            )

        if max_pu > self.thresholds["swell_pu"]:
            detections.append(
                Detection(
                    disturbance=DisturbanceType.SWELL,
                    severity="warning",
                    evidence=f"Maximum phase RMS is {max_pu:.3f} pu",
                )
            )

        if max_thd > self.thresholds["thd_percent"]:
            detections.append(
                Detection(
                    disturbance=DisturbanceType.HARMONIC_DISTORTION,
                    severity="warning",
                    evidence=f"Maximum phase THD is {max_thd:.2f}%",
                )
            )

        if unbalance > self.thresholds["unbalance_percent"]:
            detections.append(
                Detection(
                    disturbance=DisturbanceType.PHASE_UNBALANCE,
                    severity="warning",
                    evidence=f"Negative/positive sequence ratio is {unbalance:.2f}%",
                )
            )

        priority = (
            DisturbanceType.INTERRUPTION,
            DisturbanceType.SAG,
            DisturbanceType.SWELL,
            DisturbanceType.HARMONIC_DISTORTION,
            DisturbanceType.PHASE_UNBALANCE,
        )
        detected_types = {item.disturbance for item in detections}
        primary = next(
            (disturbance for disturbance in priority if disturbance in detected_types),
            DisturbanceType.NOMINAL,
        )

        phase_metrics = [
            PhaseMetrics(
                rms_v=round(rms_values[index], 3),
                rms_pu=round(rms_pu[index], 4),
                thd_percent=round(thd_values[index], 3),
            )
            for index in range(3)
        ]
        return AnalysisResult(
            primary_class=primary,
            phase_a=phase_metrics[0],
            phase_b=phase_metrics[1],
            phase_c=phase_metrics[2],
            voltage_unbalance_percent=round(float(unbalance), 3),
            detections=detections,
            thresholds=self.thresholds,
        )

