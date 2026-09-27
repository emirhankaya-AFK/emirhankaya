"""Small worked studies used by the API and dashboard."""

from .models import CoordinationStudy, CurveType, RelaySetting


def coordinated_feeder() -> CoordinationStudy:
    return CoordinationStudy(
        required_margin_s=0.30,
        relays=[
            RelaySetting(
                name="R3",
                location="Workshop feeder",
                pickup_a=180,
                time_multiplier=0.10,
                curve=CurveType.STANDARD_INVERSE,
                fault_current_a=1800,
            ),
            RelaySetting(
                name="R2",
                location="Main LV board",
                pickup_a=240,
                time_multiplier=0.24,
                curve=CurveType.STANDARD_INVERSE,
                fault_current_a=1800,
            ),
            RelaySetting(
                name="R1",
                location="Transformer incomer",
                pickup_a=300,
                time_multiplier=0.42,
                curve=CurveType.STANDARD_INVERSE,
                fault_current_a=1800,
            ),
        ],
    )


def miscoordinated_feeder() -> CoordinationStudy:
    study = coordinated_feeder()
    study.relays[1].time_multiplier = 0.12
    study.relays[2].time_multiplier = 0.18
    return study
