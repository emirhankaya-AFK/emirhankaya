"""Domain models for sampled three-phase signals and analysis results."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class DisturbanceType(StrEnum):
    NOMINAL = "nominal"
    INTERRUPTION = "interruption"
    SAG = "voltage_sag"
    SWELL = "voltage_swell"
    HARMONIC_DISTORTION = "harmonic_distortion"
    PHASE_UNBALANCE = "phase_unbalance"


class SignalWindow(BaseModel):
    """A fixed-rate waveform window with phase-to-neutral voltage samples."""

    sample_rate_hz: float = Field(gt=100)
    nominal_frequency_hz: float = Field(default=50.0, gt=0)
    nominal_voltage_rms: float = Field(default=230.0, gt=0)
    voltage_a: list[float] = Field(min_length=64)
    voltage_b: list[float] = Field(min_length=64)
    voltage_c: list[float] = Field(min_length=64)

    @model_validator(mode="after")
    def validate_lengths(self) -> SignalWindow:
        lengths = {len(self.voltage_a), len(self.voltage_b), len(self.voltage_c)}
        if len(lengths) != 1:
            raise ValueError("All phase arrays must have equal length")
        return self


class PhaseMetrics(BaseModel):
    rms_v: float
    rms_pu: float
    thd_percent: float


class Detection(BaseModel):
    disturbance: DisturbanceType
    severity: str
    evidence: str


class AnalysisResult(BaseModel):
    primary_class: DisturbanceType
    phase_a: PhaseMetrics
    phase_b: PhaseMetrics
    phase_c: PhaseMetrics
    voltage_unbalance_percent: float
    detections: list[Detection]
    thresholds: dict[str, float]

