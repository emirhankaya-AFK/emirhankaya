"""Coordination calculations for relays ordered from downstream to upstream."""

from .curves import operating_time_s
from .models import CoordinationPair, CoordinationStudy, RelayResult, StudyResult


def analyze_study(study: CoordinationStudy) -> StudyResult:
    relay_results: list[RelayResult] = []
    raw_times: list[float | None] = []

    for relay in study.relays:
        multiple = relay.fault_current_a / relay.pickup_a
        trip_time = operating_time_s(
            relay.fault_current_a,
            relay.pickup_a,
            relay.time_multiplier,
            relay.curve,
        )
        raw_times.append(trip_time)
        relay_results.append(
            RelayResult(
                name=relay.name,
                location=relay.location,
                multiple_of_pickup=round(multiple, 3),
                operates=trip_time is not None,
                operating_time_s=round(trip_time, 4) if trip_time is not None else None,
                note=(
                    "Pickup exceeded; inverse-time equation evaluated."
                    if trip_time is not None
                    else "Fault current does not exceed pickup."
                ),
            )
        )

    pairs: list[CoordinationPair] = []
    for index in range(len(study.relays) - 1):
        downstream = study.relays[index]
        upstream = study.relays[index + 1]
        downstream_time = raw_times[index]
        upstream_time = raw_times[index + 1]
        if downstream_time is None or upstream_time is None:
            margin = None
            coordinated = False
            note = "Margin cannot be checked because one relay does not operate."
        else:
            margin = upstream_time - downstream_time
            coordinated = margin >= study.required_margin_s
            note = (
                "Required grading margin is met."
                if coordinated
                else "Upstream delay is too short for the required grading margin."
            )
        pairs.append(
            CoordinationPair(
                downstream=downstream.name,
                upstream=upstream.name,
                margin_s=round(margin, 4) if margin is not None else None,
                required_margin_s=study.required_margin_s,
                coordinated=coordinated,
                note=note,
            )
        )

    return StudyResult(
        relay_results=relay_results,
        coordination_pairs=pairs,
        all_coordinated=all(pair.coordinated for pair in pairs),
    )
