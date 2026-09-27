"""Seeded synthetic three-phase waveform generator."""

from __future__ import annotations

import numpy as np

from .models import DisturbanceType, SignalWindow


class SignalSimulator:
    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)

    def generate(
        self,
        disturbance: DisturbanceType = DisturbanceType.NOMINAL,
        *,
        cycles: int = 10,
        sample_rate_hz: float = 6400.0,
        frequency_hz: float = 50.0,
        nominal_voltage_rms: float = 230.0,
        noise_percent: float = 0.15,
    ) -> SignalWindow:
        sample_count = int(cycles * sample_rate_hz / frequency_hz)
        time = np.arange(sample_count) / sample_rate_hz
        peak = nominal_voltage_rms * np.sqrt(2.0)
        amplitudes = np.ones(3)

        if disturbance == DisturbanceType.SAG:
            amplitudes[:] = 0.70
        elif disturbance == DisturbanceType.SWELL:
            amplitudes[:] = 1.20
        elif disturbance == DisturbanceType.INTERRUPTION:
            amplitudes[:] = 0.03
        elif disturbance == DisturbanceType.PHASE_UNBALANCE:
            amplitudes[:] = [1.0, 0.94, 1.06]

        phases = []
        offsets = [0.0, -2 * np.pi / 3, 2 * np.pi / 3]
        for index, offset in enumerate(offsets):
            signal = amplitudes[index] * peak * np.sin(2 * np.pi * frequency_hz * time + offset)
            if disturbance == DisturbanceType.HARMONIC_DISTORTION:
                signal += 0.12 * peak * np.sin(2 * np.pi * 3 * frequency_hz * time + offset)
                signal += 0.08 * peak * np.sin(2 * np.pi * 5 * frequency_hz * time + offset)
            noise = self.rng.normal(0.0, peak * noise_percent / 100.0, sample_count)
            phases.append((signal + noise).tolist())

        return SignalWindow(
            sample_rate_hz=sample_rate_hz,
            nominal_frequency_hz=frequency_hz,
            nominal_voltage_rms=nominal_voltage_rms,
            voltage_a=phases[0],
            voltage_b=phases[1],
            voltage_c=phases[2],
        )
