"""Public package interface for the power-quality analyzer."""

from .analyzer import PowerQualityAnalyzer
from .models import AnalysisResult, Detection, DisturbanceType, PhaseMetrics, SignalWindow
from .simulator import SignalSimulator

__version__ = "0.1.0"

__all__ = [
    "AnalysisResult",
    "Detection",
    "DisturbanceType",
    "PhaseMetrics",
    "PowerQualityAnalyzer",
    "SignalSimulator",
    "SignalWindow",
]
