"""Analysis module for rowing data - works with both live and historical sessions."""

from dataclasses import asdict
from pathlib import Path
import pandas as pd
from rowing_data import RowingDataPoint


class RowingAnalyzer:
    """Shared analysis functions for live and historical rowing data."""
    
    @staticmethod
    def calculate_stats(df: pd.DataFrame) -> dict:
        """
        Calculate statistics from rowing DataFrame.
        Works with both live and historical data.
        
        Args:
            df: DataFrame with RowingDataPoint columns
            
        Returns:
            Dictionary with computed statistics
        """
        if df.empty:
            return {}
        
        return {
            "num_strokes": len(df),
            "total_distance_m": df['stroke_distance_m'].sum(),
            "total_duration_secs": df['stroke_duration_secs'].sum(),
            "mean_time_500m_secs": df['time_500m_secs'].mean(),
            "min_time_500m_secs": df['time_500m_secs'].min(),
            "max_time_500m_secs": df['time_500m_secs'].max(),
            "mean_strokes_per_min": df['strokes_per_min'].mean(),
            "max_strokes_per_min": df['strokes_per_min'].max(),
            "mean_power_watts": df['power_watts'].mean(),
            "max_power_watts": df['power_watts'].max(),
            "min_power_watts": df['power_watts'].min(),
            "total_calories": df['calories_per_hour'].sum(),
            "mean_resistance": df['resistance_level'].mean(),
        }
    
    @staticmethod
    def get_live_stats(data_points: list[RowingDataPoint]) -> dict:
        """
        Analyze live session data.
        
        Args:
            data_points: List of RowingDataPoint objects from current session
            
        Returns:
            Dictionary with computed statistics
        """
        if not data_points:
            return {}
        
        df = pd.DataFrame([asdict(p) for p in data_points])
        return RowingAnalyzer.calculate_stats(df)
    
    @staticmethod
    def get_historical_stats(filepath: Path) -> dict:
        """
        Analyze historical session from parquet file.
        
        Args:
            filepath: Path to parquet file
            
        Returns:
            Dictionary with computed statistics
        """
        if isinstance(filepath, str):
            filepath = Path(filepath)
        
        if not filepath.exists():
            return {}
        
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
    def compare_sessions(filepath1: Path, filepath2: Path) -> dict:
        """
        Compare statistics between two sessions.
        
        Args:
            filepath1: Path to first session
            filepath2: Path to second session
            
        Returns:
            Dictionary with stats for both sessions and differences
        """
        stats1 = RowingAnalyzer.get_historical_stats(filepath1)
        stats2 = RowingAnalyzer.get_historical_stats(filepath2)
        
        if not stats1 or not stats2:
            return {}
        
        return {
            "session1": stats1,
            "session2": stats2,
            "distance_diff_m": stats2['total_distance_m'] - stats1['total_distance_m'],
            "power_diff_watts": stats2['mean_power_watts'] - stats1['mean_power_watts'],
            "pace_diff_secs": stats2['mean_time_500m_secs'] - stats1['mean_time_500m_secs'],
        }


# Example usage
if __name__ == "__main__":
    from rowing_data import RowingSession
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
