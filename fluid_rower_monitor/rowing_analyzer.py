"""Analysis module for rowing data - works with both live and historical sessions."""

from dataclasses import asdict, dataclass
from pathlib import Path
import pandas as pd
from .rowing_data import RowingDataPoint, SessionStats
from .columns import (
    STROKE_DISTANCE_M,
    STROKE_DURATION_SECS,
    TIME_500M_SECS,
    STROKES_PER_MIN,
    POWER_WATTS,
    CALORIES_PER_HOUR,
    RESISTANCE_LEVEL,
)


@dataclass
class SessionComparison:
    """Comparison between two rowing sessions."""
    session1: SessionStats
    session2: SessionStats
    distance_diff_m: float
    power_diff_watts: float
    pace_diff_secs: float


class RowingAnalyzer:
    """Shared analysis functions for live and historical rowing data."""
    
    @staticmethod
    def calculate_stats(df: pd.DataFrame) -> SessionStats | None:
        """
        Calculate statistics from rowing DataFrame.
        Works with both live and historical data.
        
        Args:
            df: DataFrame with RowingDataPoint columns
            
        Returns:
            SessionStats object with computed statistics, or None if empty
        """
        if df.empty:
            return None
        
        return SessionStats(
            num_strokes=len(df),
            total_distance_m=df[STROKE_DISTANCE_M].sum(),
            total_duration_secs=df[STROKE_DURATION_SECS].sum(),
            mean_time_500m_secs=df[TIME_500M_SECS].mean(),
            min_time_500m_secs=df[TIME_500M_SECS].min(),
            max_time_500m_secs=df[TIME_500M_SECS].max(),
            mean_strokes_per_min=df[STROKES_PER_MIN].mean(),
            max_strokes_per_min=df[STROKES_PER_MIN].max(),
            mean_power_watts=df[POWER_WATTS].mean(),
            max_power_watts=df[POWER_WATTS].max(),
            min_power_watts=df[POWER_WATTS].min(),
            total_calories=df[CALORIES_PER_HOUR].sum(),
            mean_resistance=df[RESISTANCE_LEVEL].mean(),
        )
    
    @staticmethod
    def get_live_stats(data_points: list[RowingDataPoint]) -> SessionStats | None:
        """
        Analyze live session data.
        
        Args:
            data_points: List of RowingDataPoint objects from current session
            
        Returns:
            SessionStats object with computed statistics, or None if empty
        """
        if not data_points:
            return None
        
        df = pd.DataFrame([asdict(p) for p in data_points])
        return RowingAnalyzer.calculate_stats(df)
    
    @staticmethod
    def get_historical_stats(filepath: Path) -> SessionStats | None:
        """
        Analyze historical session from parquet file.
        
        Args:
            filepath: Path to parquet file
            
        Returns:
            SessionStats object with computed statistics, or None if file doesn't exist
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        if not filepath.exists():
            return None
        
        df = pd.read_parquet(filepath)
        return RowingAnalyzer.calculate_stats(df)
    
    @staticmethod
    def get_live_dataframe(data_points: list[RowingDataPoint]) -> pd.DataFrame:
        """Convert live data points to DataFrame for custom analysis."""
        if not data_points:
            return pd.DataFrame()
        return pd.DataFrame([asdict(p) for p in data_points])
    
    @staticmethod
    def get_historical_dataframe(filepath: Path) -> pd.DataFrame:
        """Load historical session as DataFrame for custom analysis."""
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        if not filepath.exists():
            return pd.DataFrame()
        
        return pd.read_parquet(filepath)
    
    @staticmethod
    def compare_sessions(filepath1: Path, filepath2: Path) -> SessionComparison | None:
        """
        Compare statistics between two sessions.
        
        Args:
            filepath1: Path to first session
            filepath2: Path to second session
            
        Returns:
            SessionComparison with stats for both sessions and differences, or None if either file doesn't exist
        """
        stats1 = RowingAnalyzer.get_historical_stats(filepath1)
        stats2 = RowingAnalyzer.get_historical_stats(filepath2)
        
        if not stats1 or not stats2:
            return None
        
        return SessionComparison(
            session1=stats1,
            session2=stats2,
            distance_diff_m=stats2.total_distance_m - stats1.total_distance_m,
            power_diff_watts=stats2.mean_power_watts - stats1.mean_power_watts,
            pace_diff_secs=stats2.mean_time_500m_secs - stats1.mean_time_500m_secs,
        )


# Example usage
if __name__ == "__main__":
    from .rowing_data import RowingSession
    from datetime import datetime
    
    # Create sample live data
    session = RowingSession()
    for i in range(5):
        point = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.1,
            time_500m_secs=139 - i,
            strokes_per_min=22 + i,
            power_watts=129 + i,
            calories_per_hour=744,
            resistance_level=9,
        )
        session.add_point(point)
    
    # Analyze live
    print("Live stats:", RowingAnalyzer.get_live_stats(session.data_points))
    
    # Save and analyze historical
    session.save()
    print("Historical stats:", RowingAnalyzer.get_historical_stats(session.filename))
