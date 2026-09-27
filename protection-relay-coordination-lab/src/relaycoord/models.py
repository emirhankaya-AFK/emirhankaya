"""Validated inputs and outputs for a radial-feeder coordination study."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class CurveType(StrEnum):
    STANDARD_INVERSE = "standard_inverse"
    VERY_INVERSE = "very_inverse"
    EXTREMELY_INVERSE = "extremely_inverse"


class RelaySetting(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    location: str = Field(min_length=1, max_length=80)
    pickup_a: float = Field(gt=0)
    time_multiplier: float = Field(gt=0, le=2)
    curve: CurveType = CurveType.STANDARD_INVERSE
    fault_current_a: float = Field(gt=0)


class CoordinationStudy(BaseModel):
    relays: list[RelaySetting] = Field(min_length=2, max_length=12)
    required_margin_s: float = Field(default=0.30, ge=0.10, le=1.0)

    @model_validator(mode="after")
    def relay_names_must_be_unique(self):
        names = [relay.name.casefold() for relay in self.relays]
        if len(names) != len(set(names)):
            raise ValueError("Relay names must be unique")
        return self


class RelayResult(BaseModel):
    name: str
    location: str
    multiple_of_pickup: float
    operates: bool
    operating_time_s: float | None
    note: str


class CoordinationPair(BaseModel):
    downstream: str
    upstream: str
    margin_s: float | None
    required_margin_s: float
    coordinated: bool
    note: str


class StudyResult(BaseModel):
    relay_results: list[RelayResult]
    coordination_pairs: list[CoordinationPair]
    all_coordinated: bool
