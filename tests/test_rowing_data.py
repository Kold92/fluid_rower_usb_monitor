"""Tests for rowing_data module - data models and session storage."""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import shutil
from fluid_rower_monitor.rowing_data import RowingDataPoint, RowingSession


class TestRowingDataPoint:
    """Test the RowingDataPoint dataclass."""

    def test_create_rowing_data_point(self):
        """Test creating a RowingDataPoint."""
        point = RowingDataPoint(
            stroke_duration_secs=2.3,
            stroke_distance_m=9.1,
            time_500m_secs=139,
            strokes_per_min=22,
            power_watts=129,
            calories_per_hour=744,
            resistance_level=9,
        )

        assert point.stroke_duration_secs == 2.3
        assert point.stroke_distance_m == 9.1
        assert point.time_500m_secs == 139
        assert point.strokes_per_min == 22
        assert point.power_watts == 129
        assert point.calories_per_hour == 744
        assert point.resistance_level == 9

    def test_rowing_data_point_defaults(self):
        """Test that all fields are required (no defaults)."""
        with pytest.raises(TypeError):
            RowingDataPoint(stroke_duration_secs=2.3)  # Missing other fields

    def test_multiple_rowing_data_points(self):
        """Test creating multiple RowingDataPoint objects."""
        points = []
        for i in range(5):
            point = RowingDataPoint(
                stroke_duration_secs=2.3 + i * 0.1,
                stroke_distance_m=9.1 + i * 0.2,
                time_500m_secs=139 - i,
                strokes_per_min=22 + i,
                power_watts=129 + i * 5,
                calories_per_hour=744,
                resistance_level=9,
            )
            points.append(point)

        assert len(points) == 5
        assert points[0].strokes_per_min == 22
        assert points[4].strokes_per_min == 26
        assert points[0].power_watts == 129
        assert points[4].power_watts == 149


class TestRowingSession:
    """Test the RowingSession class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_create_rowing_session(self):
        """Test creating a RowingSession."""
        session = RowingSession(data_dir=self.temp_dir)

        assert session.session_start is not None
        assert isinstance(session.session_start, datetime)
        assert session.data_points == []
        assert session.data_dir == Path(self.temp_dir)

    def test_session_with_custom_start_time(self):
        """Test creating a RowingSession with custom start time."""
        custom_time = datetime(2026, 1, 24, 10, 30, 0)
        session = RowingSession(session_start=custom_time, data_dir=self.temp_dir)

        assert session.session_start == custom_time

    def test_session_filename_format(self):
        """Test that session filename follows YYYY-MM-DD_HH-MM-SS format."""
        custom_time = datetime(2026, 1, 24, 14, 35, 45)
        session = RowingSession(session_start=custom_time, data_dir=self.temp_dir)

        expected_filename = "2026-01-24_14-35-45.parquet"
        assert session.filename.name == expected_filename

    def test_add_point_to_session(self):
        """Test adding a RowingDataPoint to a session."""
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

        assert len(session.data_points) == 1
        assert session.data_points[0] == point

    def test_add_multiple_points(self):
        """Test adding multiple RowingDataPoints to a session."""
        session = RowingSession(data_dir=self.temp_dir)

        for i in range(5):
            point = RowingDataPoint(
                stroke_duration_secs=2.3,
                stroke_distance_m=9.1 + i,
                time_500m_secs=139 - i,
                strokes_per_min=22 + i,
                power_watts=129 + i * 5,
                calories_per_hour=744,
                resistance_level=9,
            )
            session.add_point(point)

        assert len(session.data_points) == 5

    def test_session_save_creates_file(self):
        """Test that save() creates a parquet file."""
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

        assert session.filename.exists()
        assert session.filename.suffix == ".parquet"

    def test_session_save_empty_session(self, capsys):
        """Test that save() handles empty sessions gracefully."""
        session = RowingSession(data_dir=self.temp_dir)
        session.save()

        captured = capsys.readouterr()
        assert "No data points to save" in captured.out
        assert not session.filename.exists()

    def test_get_stats_single_point(self):
        """Test getting stats from a session with one point."""
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

        stats = session.get_stats()

        assert stats["num_strokes"] == 1
        assert stats["total_distance_m"] == 9.1
        assert stats["total_duration_secs"] == 2.3
        assert stats["avg_watts"] == 129
        assert stats["max_watts"] == 129
        assert stats["min_watts"] == 129
        assert stats["avg_strokes_per_min"] == 22

    def test_get_stats_multiple_points(self):
        """Test getting stats from a session with multiple points."""
        session = RowingSession(data_dir=self.temp_dir)

        for i in range(5):
            point = RowingDataPoint(
                stroke_duration_secs=2.3,
                stroke_distance_m=9.0,
                time_500m_secs=139,
                strokes_per_min=20 + i,
                power_watts=120 + i * 10,
                calories_per_hour=744,
                resistance_level=9,
            )
            session.add_point(point)

        stats = session.get_stats()

        assert stats["num_strokes"] == 5
        assert stats["total_distance_m"] == 45.0
        assert stats["total_duration_secs"] == 11.5
        assert stats["avg_watts"] == 140.0  # Average of 120, 130, 140, 150, 160
        assert stats["max_watts"] == 160
        assert stats["min_watts"] == 120
        assert stats["avg_strokes_per_min"] == 22.0

    def test_get_stats_empty_session(self):
        """Test getting stats from an empty session."""
        session = RowingSession(data_dir=self.temp_dir)
        stats = session.get_stats()

        assert stats == {}

    def test_data_dir_created_if_not_exists(self):
        """Test that data_dir is created if it doesn't exist."""
        new_dir = Path(self.temp_dir) / "new_sessions"
        assert not new_dir.exists()

        session = RowingSession(data_dir=str(new_dir))

        assert new_dir.exists()

    def test_session_persistence(self):
        """Test that session data persists across save and load."""
        session = RowingSession(data_dir=self.temp_dir)

        for i in range(3):
            point = RowingDataPoint(
                stroke_duration_secs=2.5,
                stroke_distance_m=9.0 + i,
                time_500m_secs=140 - i,
                strokes_per_min=22,
                power_watts=130 + i * 5,
                calories_per_hour=750,
                resistance_level=8,
            )
            session.add_point(point)

        session.save()

        # Load the saved file and verify
        import pandas as pd
        loaded_df = pd.read_parquet(session.filename)

        assert len(loaded_df) == 3
        assert loaded_df["stroke_distance_m"].tolist() == [9.0, 10.0, 11.0]
