from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

# Reuse existing validated settings models from the core package
from ..settings import (
    AppSettings,
    SerialSettings,
    DataSettings,
    LoggingSettings,
    ReconnectSettings,
    UISettings,
)


class ErrorResponse(BaseModel):
    code: int = Field(..., description="Application-specific error code")
    message: str = Field(..., description="Human-readable error")


class Config(BaseModel):
    """API model mirroring `AppSettings` structure for GET/PUT endpoints."""

    version: int = 1
    serial: SerialSettings = SerialSettings()
    data: DataSettings = DataSettings()
    logging: LoggingSettings = LoggingSettings()
    reconnect: ReconnectSettings = ReconnectSettings()
    ui: UISettings = UISettings()

    @classmethod
    def from_app_settings(cls, settings: AppSettings) -> "Config":
        return cls(
            version=settings.version,
            serial=settings.serial,
            data=settings.data,
            logging=settings.logging,
            reconnect=settings.reconnect,
            ui=settings.ui,
        )


class UIPreferences(BaseModel):
    """UI configuration preferences (deprecated - use UISettings from settings)."""

    x_axis_type: Literal["samples", "time", "distance"] = Field(
        default="samples",
        description=(
            "X-axis display mode for charts: samples (stroke number), time (elapsed seconds), "
            "distance (cumulative meters)"
        ),
    )


class SessionSummary(BaseModel):
    id: str = Field(..., description="Session identifier (filename)")
    start: Optional[datetime] = Field(None, description="Parsed session start time from filename")
    num_strokes: Optional[int] = Field(None, description="Number of strokes (if quickly derivable)")
    total_distance_m: Optional[float] = Field(None, description="Total distance (optional)")


class SessionDetail(BaseModel):
    id: str
    start: Optional[datetime] = None
    stats: Optional[dict] = Field(None, description="Computed statistics for the session")
    # In future we may add a few sample rows or a link to download


class ActiveSession(BaseModel):
    id: str = Field(..., description="Active session identifier (filename)")
    start: datetime = Field(..., description="Session start time")
    is_active: bool = Field(True, description="Whether session is currently active")


class LiveSample(BaseModel):
    stroke_duration_secs: float
    stroke_distance_m: float
    cumulative_duration_secs: float | None = None
    cumulative_distance_m: float | None = None
    time_500m_secs: int
    strokes_per_min: int
    power_watts: int
    calories_per_hour: int
    resistance_level: int


class LiveStats(BaseModel):
    num_strokes: int
    total_distance_m: float
    total_duration_secs: float
    avg_watts: float
    max_watts: int
    min_watts: int
    avg_time_500m_secs: float
    avg_strokes_per_min: float
    max_strokes_per_min: int
    total_calories: float
    avg_resistance: float
