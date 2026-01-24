"""Tests for rowing_analyzer module - analysis and statistics."""

import pytest
from pathlib import Path
import tempfile
import shutil
import pandas as pd
from datetime import datetime
from fluid_rower_monitor.rowing_analyzer import RowingAnalyzer
from fluid_rower_monitor.rowing_data import RowingDataPoint, RowingSession, SessionStats


class TestRowingAnalyzerCalculateStats:
    """Test RowingAnalyzer.calculate_stats method."""

    def test_calculate_stats_empty_dataframe(self):
        """Test calculate_stats with empty DataFrame."""
        df = pd.DataFrame()
        result = RowingAnalyzer.calculate_stats(df)

        assert result is None

    def test_calculate_stats_single_stroke(self):
        """Test calculate_stats with a single stroke."""
        data = {
            "stroke_duration_secs": [2.3],
            "stroke_distance_m": [9.1],
            "time_500m_secs": [139],
            "strokes_per_min": [22],
            "power_watts": [129],
            "calories_per_hour": [744],
            "resistance_level": [9],
        }
        df = pd.DataFrame(data)
        result = RowingAnalyzer.calculate_stats(df)

        assert result.num_strokes == 1
        assert result.total_distance_m == 9.1
        assert result.total_duration_secs == 2.3
        assert result.mean_time_500m_secs == 139
        assert result.min_time_500m_secs == 139
        assert result.max_time_500m_secs == 139
        assert result.mean_strokes_per_min == 22
        assert result.max_strokes_per_min == 22
        assert result.mean_power_watts == 129
        assert result.max_power_watts == 129
        assert result.min_power_watts == 129
        assert result.total_calories == 744
        assert result.mean_resistance == 9

    def test_calculate_stats_multiple_strokes(self):
        """Test calculate_stats with multiple strokes."""
        data = {
            "stroke_duration_secs": [2.3, 2.3, 2.3],
            "stroke_distance_m": [9.0, 10.0, 8.5],
            "time_500m_secs": [140, 138, 142],
            "strokes_per_min": [22, 23, 21],
            "power_watts": [130, 140, 120],
            "calories_per_hour": [750, 750, 750],
            "resistance_level": [9, 9, 9],
        }
        df = pd.DataFrame(data)
        result = RowingAnalyzer.calculate_stats(df)

        assert result.num_strokes == 3
        assert result.total_distance_m == 27.5
        assert abs(result.total_duration_secs - 6.9) < 0.0001  # Use approximate comparison
        assert result.mean_time_500m_secs == 140.0
        assert result.min_time_500m_secs == 138
        assert result.max_time_500m_secs == 142
        assert result.mean_strokes_per_min == 22.0
        assert result.max_strokes_per_min == 23
        assert result.mean_power_watts == 130.0
        assert result.max_power_watts == 140
        assert result.min_power_watts == 120
        assert result.total_calories == 2250

    def test_calculate_stats_has_all_fields(self):
        """Test that calculate_stats returns all expected fields."""
        data = {
            "stroke_duration_secs": [2.3],
            "stroke_distance_m": [9.1],
            "time_500m_secs": [139],
            "strokes_per_min": [22],
            "power_watts": [129],
            "calories_per_hour": [744],
            "resistance_level": [9],
        }
        df = pd.DataFrame(data)
        result = RowingAnalyzer.calculate_stats(df)

        assert isinstance(result, SessionStats)
        assert hasattr(result, 'num_strokes')
        assert hasattr(result, 'total_distance_m')
        assert hasattr(result, 'total_duration_secs')
        assert hasattr(result, 'mean_time_500m_secs')
        assert hasattr(result, 'min_time_500m_secs')
        assert hasattr(result, 'max_time_500m_secs')
        assert hasattr(result, 'mean_strokes_per_min')
        assert hasattr(result, 'max_strokes_per_min')
        assert hasattr(result, 'mean_power_watts')
        assert hasattr(result, 'max_power_watts')
        assert hasattr(result, 'min_power_watts')
        assert hasattr(result, 'total_calories')
        assert hasattr(result, 'mean_resistance')


class TestRowingAnalyzerLiveStats:
    """Test RowingAnalyzer.get_live_stats method."""

    def test_get_live_stats_empty_list(self):
        """Test get_live_stats with empty list."""
        result = RowingAnalyzer.get_live_stats([])

        assert result is None

    def test_get_live_stats_single_point(self):
        """Test get_live_stats with a single RowingDataPoint."""
        point = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.1,
            time_500m_secs=139,
            strokes_per_min=22,
            power_watts=129,
            calories_per_hour=744,
            resistance_level=9,
        )
        result = RowingAnalyzer.get_live_stats([point])

        assert result.num_strokes == 1
        assert result.total_distance_m == 9.1
        assert result.mean_power_watts == 129

    def test_get_live_stats_multiple_points(self):
        """Test get_live_stats with multiple RowingDataPoints."""
        points = []
        for i in range(5):
            point = RowingDataPoint(
                stroke_duration_secs=2.3,
                stroke_distance_m=9.0 + i,
                time_500m_secs=140 - i,
                strokes_per_min=22,
                power_watts=130 + i * 10,
                calories_per_hour=750,
                resistance_level=9,
            )
            points.append(point)

        result = RowingAnalyzer.get_live_stats(points)

        assert result.num_strokes == 5
        # Distances: 9.0, 10.0, 11.0, 12.0, 13.0 = 55.0
        assert result.total_distance_m == 55.0
        assert result.mean_power_watts == 150.0


class TestRowingAnalyzerHistoricalStats:
    """Test RowingAnalyzer.get_historical_stats method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_get_historical_stats_nonexistent_file(self):
        """Test get_historical_stats with nonexistent file."""
        filepath = Path(self.temp_dir) / "nonexistent.parquet"
        result = RowingAnalyzer.get_historical_stats(filepath)

        assert result is None

    def test_get_historical_stats_string_path(self):
        """Test get_historical_stats with string path."""
        # Create a session and save it
        session = RowingSession(data_dir=self.temp_dir)
        point = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.1,
            time_500m_secs=139,
            strokes_per_min=22,
            power_watts=129,
            calories_per_hour=744,
            resistance_level=9,
        )
        session.add_point(point)
        session.save()

        # Test with string path
        result = RowingAnalyzer.get_historical_stats(str(session.filename))

        assert result.num_strokes == 1
        assert result.total_distance_m == 9.1

    def test_get_historical_stats_path_object(self):
        """Test get_historical_stats with Path object."""
        session = RowingSession(data_dir=self.temp_dir)
        point = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.1,
            time_500m_secs=139,
            strokes_per_min=22,
            power_watts=129,
            calories_per_hour=744,
            resistance_level=9,
        )
        session.add_point(point)
        session.save()

        result = RowingAnalyzer.get_historical_stats(session.filename)

        assert result.num_strokes == 1
        assert result.total_distance_m == 9.1

    def test_get_historical_stats_multiple_points(self):
        """Test get_historical_stats with multiple points saved."""
        session = RowingSession(data_dir=self.temp_dir)

        for i in range(5):
            point = RowingDataPoint(
                stroke_duration_secs=2.3,
                stroke_distance_m=9.0 + i,
                time_500m_secs=140 - i,
                strokes_per_min=22,
                power_watts=130 + i * 10,
                calories_per_hour=750,
                resistance_level=9,
            )
            session.add_point(point)

        session.save()
        result = RowingAnalyzer.get_historical_stats(session.filename)

        assert result.num_strokes == 5
        # Distances: 9.0, 10.0, 11.0, 12.0, 13.0 = 55.0
        assert result.total_distance_m == 55.0


class TestRowingAnalyzerDataFrameMethods:
    """Test RowingAnalyzer DataFrame conversion methods."""

    def test_get_live_dataframe_empty(self):
        """Test get_live_dataframe with empty list."""
        df = RowingAnalyzer.get_live_dataframe([])

        assert df.empty

    def test_get_live_dataframe_single_point(self):
        """Test get_live_dataframe with single point."""
        point = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.1,
            time_500m_secs=139,
            strokes_per_min=22,
            power_watts=129,
            calories_per_hour=744,
            resistance_level=9,
        )
        df = RowingAnalyzer.get_live_dataframe([point])

        assert len(df) == 1
        assert df["stroke_distance_m"].iloc[0] == 9.1
        assert df["power_watts"].iloc[0] == 129

    def test_get_live_dataframe_multiple_points(self):
        """Test get_live_dataframe with multiple points."""
        points = []
        for i in range(3):
            point = RowingDataPoint(
                stroke_duration_secs=2.3,
                stroke_distance_m=9.0 + i,
                time_500m_secs=140 - i,
                strokes_per_min=22,
                power_watts=130 + i * 10,
                calories_per_hour=750,
                resistance_level=9,
            )
            points.append(point)

        df = RowingAnalyzer.get_live_dataframe(points)

        assert len(df) == 3
        assert df["stroke_distance_m"].tolist() == [9.0, 10.0, 11.0]


class TestRowingAnalyzerCompareSessions:
    """Test RowingAnalyzer.compare_sessions method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_compare_sessions_both_valid(self):
        """Test comparing two valid sessions."""
        # Session 1
        session1 = RowingSession(session_start=datetime(2026, 1, 24, 10, 0), data_dir=self.temp_dir)
        point1 = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.0,
            time_500m_secs=140,
            strokes_per_min=22,
            power_watts=130,
            calories_per_hour=750,
            resistance_level=9,
        )
        session1.add_point(point1)
        session1.save()

        # Session 2 - slightly better performance
        session2 = RowingSession(session_start=datetime(2026, 1, 24, 11, 0), data_dir=self.temp_dir)
        point2 = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=10.0,
            time_500m_secs=135,
            strokes_per_min=24,
            power_watts=150,
            calories_per_hour=780,
            resistance_level=9,
        )
        session2.add_point(point2)
        session2.save()

        # Compare
        result = RowingAnalyzer.compare_sessions(session1.filename, session2.filename)

        assert "session1" in result
        assert "session2" in result
        assert result["distance_diff_m"] == 1.0
        assert result["power_diff_watts"] == 20.0
        assert result["pace_diff_secs"] == -5  # Session 2 is 5 seconds faster

    def test_compare_sessions_nonexistent(self):
        """Test comparing when one or both files don't exist."""
        nonexistent1 = Path(self.temp_dir) / "nonexistent1.parquet"
        nonexistent2 = Path(self.temp_dir) / "nonexistent2.parquet"

        result = RowingAnalyzer.compare_sessions(nonexistent1, nonexistent2)

        assert result is None

    def test_compare_sessions_first_invalid(self):
        """Test comparing when first session doesn't exist."""
        # Create only session 2
        session2 = RowingSession(data_dir=self.temp_dir)
        point = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.0,
            time_500m_secs=140,
            strokes_per_min=22,
            power_watts=130,
            calories_per_hour=750,
            resistance_level=9,
        )
        session2.add_point(point)
        session2.save()

        nonexistent = Path(self.temp_dir) / "nonexistent.parquet"
        result = RowingAnalyzer.compare_sessions(nonexistent, session2.filename)

        assert result is None
