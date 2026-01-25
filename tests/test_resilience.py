"""Tests for Phase 1.5 resilience features: pause/resume, partial saves, flush triggers."""

import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from fluid_rower_monitor.rowing_data import RowingSession, RowingDataPoint
from fluid_rower_monitor.settings import AppSettings


class TestSessionPauseResume:
    """Test pause/resume tracking for disconnection resilience."""

    def test_session_pause_sets_timestamp(self):
        """Test that pause() records a pause timestamp."""
        session = RowingSession()
        assert session.paused_at is None

        session.pause()

        assert session.paused_at is not None
        assert isinstance(session.paused_at, datetime)

    def test_session_resume_after_pause(self):
        """Test that resume() completes a pause and records duration."""
        session = RowingSession()
        session.pause()
        pause_time = session.paused_at

        session.resume()

        assert session.paused_at is None
        assert len(session.pauses) == 1
        paused_at, resumed_at = session.pauses[0]
        assert paused_at == pause_time
        assert resumed_at is not None
        assert isinstance(session.total_pause_secs, float)
        assert session.total_pause_secs > 0

    def test_multiple_pause_resume_cycles(self):
        """Test multiple pause/resume cycles accumulate."""
        session = RowingSession()

        for i in range(3):
            session.pause()
            session.resume()

        assert len(session.pauses) == 3
        assert session.total_pause_secs > 0

    def test_resume_without_pause_is_noop(self):
        """Test that resume() without pause() is safe."""
        session = RowingSession()
        session.resume()  # Should not raise
        assert len(session.pauses) == 0
        assert session.total_pause_secs == 0

    def test_pause_while_already_paused_is_idempotent(self):
        """Test that pause() while already paused doesn't create duplicate."""
        session = RowingSession()
        session.pause()
        first_pause = session.paused_at

        session.pause()  # Should be idempotent

        assert session.paused_at == first_pause
        assert len(session.pauses) == 0  # Not resumed yet


class TestSessionPartialSave:
    """Test partial save / flush functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_partial_save_creates_file(self):
        """Test that partial_save() creates a parquet file."""
        session = RowingSession(data_dir=self.temp_dir)

        for i in range(3):
            point = RowingDataPoint(
                stroke_duration_secs=2.0,
                stroke_distance_m=10.0,
                time_500m_secs=140,
                strokes_per_min=20,
                power_watts=100,
                calories_per_hour=600,
                resistance_level=5,
            )
            session.add_point(point)

        session.partial_save(from_index=0)

        assert session.filename.exists()

    def test_partial_save_appends_to_existing(self):
        """Test that partial_save() appends to existing file."""
        session = RowingSession(data_dir=self.temp_dir)

        # First batch
        for i in range(2):
            point = RowingDataPoint(
                stroke_duration_secs=2.0,
                stroke_distance_m=10.0,
                time_500m_secs=140,
                strokes_per_min=20,
                power_watts=100 + i,
                calories_per_hour=600,
                resistance_level=5,
            )
            session.add_point(point)

        session.partial_save(from_index=0)

        # Second batch
        for i in range(2, 4):
            point = RowingDataPoint(
                stroke_duration_secs=2.0,
                stroke_distance_m=10.0,
                time_500m_secs=140,
                strokes_per_min=20,
                power_watts=100 + i,
                calories_per_hour=600,
                resistance_level=5,
            )
            session.add_point(point)

        session.partial_save(from_index=2)

        # Verify file has all 4 rows
        import pandas as pd

        df = pd.read_parquet(session.filename)
        assert len(df) == 4
        assert df["power_watts"].tolist() == [100, 101, 102, 103]

    def test_partial_save_from_index(self):
        """Test that partial_save(from_index=N) only saves from index N onward."""
        session = RowingSession(data_dir=self.temp_dir)

        for i in range(5):
            point = RowingDataPoint(
                stroke_duration_secs=2.0,
                stroke_distance_m=10.0,
                time_500m_secs=140,
                strokes_per_min=20,
                power_watts=100 + i,
                calories_per_hour=600,
                resistance_level=5,
            )
            session.add_point(point)

        # Save only from index 2 onward
        session.partial_save(from_index=2)

        import pandas as pd

        df = pd.read_parquet(session.filename)
        assert len(df) == 3
        assert df["power_watts"].tolist() == [102, 103, 104]

    def test_partial_save_noop_if_from_index_out_of_range(self):
        """Test that partial_save() is noop if from_index >= len(data_points)."""
        session = RowingSession(data_dir=self.temp_dir)

        for i in range(3):
            point = RowingDataPoint(
                stroke_duration_secs=2.0,
                stroke_distance_m=10.0,
                time_500m_secs=140,
                strokes_per_min=20,
                power_watts=100 + i,
                calories_per_hour=600,
                resistance_level=5,
            )
            session.add_point(point)

        session.partial_save(from_index=10)

        # File should not exist
        assert not session.filename.exists()


class TestFlushTriggersInSession:
    """Test flush trigger logic integrates with rowing_session."""

    def test_flush_settings_defaults(self):
        """Test that default flush settings are reasonable."""
        settings = AppSettings()
        assert settings.reconnect.flush_interval_secs > 0
        assert settings.reconnect.flush_after_strokes > 0

    def test_flush_settings_custom(self):
        """Test that flush settings can be customized."""
        settings = AppSettings()
        settings.reconnect.flush_interval_secs = 30.0
        settings.reconnect.flush_after_strokes = 5

        assert settings.reconnect.flush_interval_secs == 30.0
        assert settings.reconnect.flush_after_strokes == 5
