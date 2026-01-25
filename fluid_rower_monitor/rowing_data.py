"""This module is used for saving and analyzing rowing data received from the device."""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import pandas as pd
import polars as pl

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
    device_type: int | None      # Device type identifier (A5 -> 5)
    cumulative_duration_secs: int  # Total time since session start
    cumulative_distance_m: int     # Total distance since session start
    time_500m_secs: int           # Current 500m pace in seconds
    strokes_per_min: int          # Current stroke rate
    power_watts: int              # Current power output
    calories_per_hour: int        # Current calorie burn rate
    resistance_level: int         # Current resistance level


@dataclass
class RowingDataPoint:
    """Single rowing stroke data point (per-stroke, not cumulative)."""
    stroke_duration_secs: float  # Duration of this stroke
    stroke_distance_m: float     # Distance covered in this stroke
    time_500m_secs: int          # Current 500m pace in seconds
    strokes_per_min: int         # Current stroke rate
    power_watts: int             # Power output for this stroke
    calories_per_hour: int       # Current calorie burn rate
    resistance_level: int        # Current resistance level


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
    
    def add_point(self, point: RowingDataPoint) -> None:
        """Add a rowing data point to the session."""
        self.data_points.append(point)
    
    def save(self) -> None:
        """Save session to parquet file."""
        if not self.data_points:
            print(f"No data points to save for session {self.session_start}")
            return
        
        # Convert dataclass to dict, then to DataFrame
        data_dicts = [asdict(p) for p in self.data_points]
        df = pd.DataFrame(data_dicts)
        
        df.to_parquet(self.filename, index=False)
        print(f"Session saved to {self.filename}")
    
    def get_stats(self) -> dict:
        """Get statistics for this session."""
        if not self.data_points:
            return {}
        
        df = pd.DataFrame([asdict(p) for p in self.data_points])
        
        return {
            "session_start": self.session_start,
            "num_strokes": len(self.data_points),
            "total_distance_m": df['stroke_distance_m'].sum(),
            "total_duration_secs": df['stroke_duration_secs'].sum(),
            "avg_watts": df['power_watts'].mean(),
            "max_watts": df['power_watts'].max(),
            "min_watts": df['power_watts'].min(),
            "avg_strokes_per_min": df['strokes_per_min'].mean(),
            "total_calories": df['calories_per_hour'].sum(),
            "avg_resistance": df['resistance_level'].mean(),
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
    def load_session(filepath: Path) -> pd.DataFrame:
        """Load a session from parquet file."""
        if isinstance(filepath, str):
            filepath = Path(filepath)
        return pd.read_parquet(filepath)
    
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
            total_distance_m=combined['stroke_distance_m'].sum(),
            avg_watts_all_time=combined['power_watts'].mean(),
            max_watts_all_time=combined['power_watts'].max(),
            total_calories=combined['calories_per_hour'].sum(),
            avg_strokes_per_min_all_time=combined['strokes_per_min'].mean(),
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