"""This module is used for saving and analyzing rowing data received from the device."""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import pandas as pd
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
from .columns import (
    STROKE_DISTANCE_M,
    STROKE_DURATION_SECS,
    STROKES_PER_MIN,
    POWER_WATTS,
    CALORIES_PER_HOUR,
    RESISTANCE_LEVEL,
)
from .migrations import apply_migrations

# Schema version for parquet files. Increment when changing data format.
# Used for data migrations when schema changes in future versions.
SCHEMA_VERSION = 1


@dataclass
class AllSessionsStats:
    """Aggregated statistics across all saved rowing sessions."""

    total_sessions: int
    total_strokes: int
    total_distance_m: float
    avg_watts_all_time: float
    max_watts_all_time: float
    total_calories: float
    avg_strokes_per_min_all_time: float


@dataclass
class RawRowingData:
    """Raw cumulative data from the rowing device (before delta calculation)."""

    device_type: int | None  # Device type identifier (A5 -> 5)
    cumulative_duration_secs: int  # Total time since session start
    cumulative_distance_m: int  # Total distance since session start
    time_500m_secs: int  # Current 500m pace in seconds
    strokes_per_min: int  # Current stroke rate
    power_watts: int  # Current power output
    calories_per_hour: int  # Current calorie burn rate
    resistance_level: int  # Current resistance level


@dataclass
class RowingDataPoint:
    """Single rowing stroke data point (per-stroke, not cumulative)."""

    stroke_duration_secs: float  # Duration of this stroke
    stroke_distance_m: float  # Distance covered in this stroke
    time_500m_secs: int  # Current 500m pace in seconds
    strokes_per_min: int  # Current stroke rate
    power_watts: int  # Power output for this stroke
    calories_per_hour: int  # Current calorie burn rate
    resistance_level: int  # Current resistance level


@dataclass
class SessionStats:
    """Statistics calculated from a rowing session."""

    num_strokes: int
    total_distance_m: float
    total_duration_secs: float
    mean_time_500m_secs: float
    min_time_500m_secs: int
    max_time_500m_secs: int
    mean_strokes_per_min: float
    max_strokes_per_min: int
    mean_power_watts: float
    max_power_watts: int
    min_power_watts: int
    total_calories: int
    mean_resistance: float


class RowingSession:
    """Manage a single rowing session with data storage and analysis."""

    def __init__(self, session_start: datetime = None, data_dir: str = "rowing_sessions"):
        """
        Initialize a rowing session.

        Args:
            session_start: Session start time (default: now)
            data_dir: Directory to store session files
        """
        self.session_start = session_start or datetime.now()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Create filename: YYYY-MM-DD_HH-MM-SS.parquet
        timestamp_str = self.session_start.strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = self.data_dir / f"{timestamp_str}.parquet"
        self.data_points: list[RowingDataPoint] = []

        # Pause/resume tracking for resilience
        self.pauses: list[tuple[datetime, datetime | None]] = []  # List of (paused_at, resumed_at)
        self.paused_at: datetime | None = None  # Current pause time, or None if not paused
        self.total_pause_secs: float = 0.0  # Cumulative pause duration

    def pause(self) -> None:
        """Mark session as paused (due to disconnection)."""
        if self.paused_at is None:
            self.paused_at = datetime.now()

    def resume(self) -> None:
        """Mark session as resumed (after reconnection)."""
        if self.paused_at is not None:
            resumed_at = datetime.now()
            pause_duration = (resumed_at - self.paused_at).total_seconds()
            self.pauses.append((self.paused_at, resumed_at))
            self.total_pause_secs += pause_duration
            self.paused_at = None

    def add_point(self, point: RowingDataPoint) -> None:
        """Add a rowing data point to the session."""
        self.data_points.append(point)

    def save(self) -> None:
        """Save session to parquet file with schema version metadata."""
        if not self.data_points:
            print(f"No data points to save for session {self.session_start}")
            return

        # Convert dataclass to dict, then to DataFrame
        data_dicts = [asdict(p) for p in self.data_points]
        df = pd.DataFrame(data_dicts)

        # Convert to Arrow table and add schema version metadata
        table = pa.Table.from_pandas(df)
        # Store schema version in file-level metadata
        table = table.replace_schema_metadata(
            {b"schema_version": str(SCHEMA_VERSION).encode(), **(table.schema.metadata or {})}
        )
        pq.write_table(table, self.filename)
        print(f"Session saved to {self.filename}")

    def partial_save(self, from_index: int = 0) -> None:
        """Save partial session data (for periodic flushing). Appends to existing file if present."""
        if from_index >= len(self.data_points):
            return

        partial_points = self.data_points[from_index:]
        if not partial_points:
            return

        data_dicts = [asdict(p) for p in partial_points]
        df_new = pd.DataFrame(data_dicts)
        table_new = pa.Table.from_pandas(df_new)

        if self.filename.exists():
            # File exists: append new rows
            df_existing = pd.read_parquet(self.filename)
            df_combined = pd.concat([df_existing, df_new], ignore_index=True)
            table_combined = pa.Table.from_pandas(df_combined)
            # Preserve schema version metadata
            table_combined = table_combined.replace_schema_metadata(
                {b"schema_version": str(SCHEMA_VERSION).encode(), **(table_combined.schema.metadata or {})}
            )
            pq.write_table(table_combined, self.filename)
        else:
            # File doesn't exist: create it with schema version metadata
            table_new = table_new.replace_schema_metadata(
                {b"schema_version": str(SCHEMA_VERSION).encode(), **(table_new.schema.metadata or {})}
            )
            pq.write_table(table_new, self.filename)

    def get_stats(self) -> dict:
        """Get statistics for this session."""
        if not self.data_points:
            return {}

        df = pd.DataFrame([asdict(p) for p in self.data_points])

        return {
            "session_start": self.session_start,
            "num_strokes": len(self.data_points),
            "total_distance_m": df[STROKE_DISTANCE_M].sum(),
            "total_duration_secs": df[STROKE_DURATION_SECS].sum(),
            "avg_watts": df[POWER_WATTS].mean(),
            "max_watts": df[POWER_WATTS].max(),
            "min_watts": df[POWER_WATTS].min(),
            "avg_strokes_per_min": df[STROKES_PER_MIN].mean(),
            "total_calories": df[CALORIES_PER_HOUR].sum(),
            "avg_resistance": df[RESISTANCE_LEVEL].mean(),
        }

    @staticmethod
    def list_sessions(data_dir: str = "rowing_sessions") -> list[Path]:
        """List all saved session files."""
        data_path = Path(data_dir)
        if not data_path.exists():
            return []
        return sorted(data_path.glob("*.parquet"))

    @staticmethod
    def delete_session(filepath: Path) -> None:
        """Delete a session file."""
        if isinstance(filepath, str):
            filepath = Path(filepath)
        filepath.unlink()
        print(f"Session deleted: {filepath}")

    @staticmethod
    def load_session(filepath: Path, auto_migrate: bool = True) -> pd.DataFrame:
        """
        Load a session from parquet file, validating schema version.

        Args:
            filepath: Path to the parquet file
            auto_migrate: If True, automatically apply migrations for older schemas

        Returns:
            DataFrame with session data

        Raises:
            ValueError: If schema version mismatch and auto_migrate=False,
                       or if migration fails
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)

        df = pd.read_parquet(filepath)

        # Validate schema version from metadata
        parquet_file = pq.ParquetFile(filepath)
        metadata = parquet_file.schema_arrow.metadata or {}
        file_schema_version = metadata.get(b"schema_version", b"1").decode("utf-8")

        try:
            file_version = int(file_schema_version)
        except (ValueError, AttributeError):
            file_version = 1  # Default to 1 if not found or invalid

        if file_version != SCHEMA_VERSION:
            if auto_migrate and file_version < SCHEMA_VERSION:
                # Apply migrations to upgrade data
                df = apply_migrations(df, file_version, SCHEMA_VERSION)
            elif file_version > SCHEMA_VERSION:
                raise ValueError(
                    f"File schema version v{file_version} is newer than "
                    f"current code v{SCHEMA_VERSION}. Please upgrade the application."
                )
            else:
                raise ValueError(
                    f"Schema version mismatch: file has v{file_version}, "
                    f"but current code expects v{SCHEMA_VERSION}. "
                    f"Set auto_migrate=True to apply migrations automatically."
                )

        return df

    @staticmethod
    def analyze_all_sessions(data_dir: str = "rowing_sessions") -> AllSessionsStats | None:
        """Analyze all sessions using Polars for fast aggregation."""
        session_files = RowingSession.list_sessions(data_dir)

        if not session_files:
            print(f"No sessions found in {data_dir}")
            return None

        # Read all parquet files with Polars
        dfs = [pl.read_parquet(str(f)) for f in session_files]
        combined = pl.concat(dfs)

        return AllSessionsStats(
            total_sessions=len(session_files),
            total_strokes=combined.shape[0],
            total_distance_m=combined[STROKE_DISTANCE_M].sum(),
            avg_watts_all_time=combined[POWER_WATTS].mean(),
            max_watts_all_time=combined[POWER_WATTS].max(),
            total_calories=combined[CALORIES_PER_HOUR].sum(),
            avg_strokes_per_min_all_time=combined[STROKES_PER_MIN].mean(),
        )


# Example usage
if __name__ == "__main__":
    # Create a session
    session = RowingSession()

    # Add some sample data points
    for i in range(10):
        point = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.1,
            time_500m_secs=139,  # 2:19 = 139 seconds
            strokes_per_min=22,
            power_watts=129 + i,
            calories_per_hour=744,
            resistance_level=9,
        )
        session.add_point(point)

    # Save session
    session.save()

    # Get session stats
    print(session.get_stats())

    # List all sessions
    print("All sessions:", RowingSession.list_sessions())

    # Analyze all sessions
    print("All sessions analysis:", RowingSession.analyze_all_sessions())
