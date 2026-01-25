"""Fluid Rower USB Monitor - Track and analyze rowing sessions."""

__version__ = "0.1.0"
__author__ = "Kold"
__description__ = "Monitor and analyze rowing sessions from a Fluid Rower device via serial connection"

from .rowing_data import RowingSession, RowingDataPoint, RawRowingData, SessionStats, AllSessionsStats
from .rowing_analyzer import RowingAnalyzer, SessionComparison

__all__ = [
    "RowingSession",
    "RowingDataPoint",
    "RawRowingData",
    "SessionStats",
    "AllSessionsStats",
    "RowingAnalyzer",
    "SessionComparison",
    "__version__",
]
