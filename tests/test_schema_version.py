"""Tests for schema version tracking in rowing data storage."""

import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from fluid_rower_monitor.rowing_data import (
    SCHEMA_VERSION,
    RowingSession,
    RowingDataPoint,
)


class TestSchemaVersion:
    """Test schema version constant and tracking."""

    def test_schema_version_exists(self):
        """SCHEMA_VERSION constant should be defined."""
        assert SCHEMA_VERSION is not None
        assert isinstance(SCHEMA_VERSION, int)

    def test_schema_version_positive(self):
        """SCHEMA_VERSION should be a positive integer."""
        assert SCHEMA_VERSION > 0

    def test_schema_version_current(self):
        """Current schema version should be 1."""
        assert SCHEMA_VERSION == 1


class TestSchemaVersionIntegration:
    """Test schema version storage and validation."""

    def test_save_stores_schema_version(self):
        """save() should store schema version in parquet metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = RowingSession(session_start=datetime(2025, 1, 20, 10, 30, 0), data_dir=tmpdir)

            # Add a data point
            point = RowingDataPoint(
                stroke_duration_secs=2.0,
                stroke_distance_m=9.0,
                time_500m_secs=140,
                strokes_per_min=22,
                power_watts=150,
                calories_per_hour=700,
                resistance_level=8,
            )
            session.add_point(point)

            # Save session
            session.save()

            # Verify file was created
            assert session.filename.exists()

            # Read metadata from parquet file using pyarrow
            parquet_file = pq.ParquetFile(session.filename)
            metadata = parquet_file.schema_arrow.metadata or {}
            schema_version_str = metadata.get(b"schema_version", b"").decode("utf-8")

            assert schema_version_str == str(SCHEMA_VERSION)

    def test_partial_save_stores_schema_version(self):
        """partial_save() should store schema version in parquet metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = RowingSession(session_start=datetime(2025, 1, 20, 10, 30, 0), data_dir=tmpdir)

            # Add data points
            for i in range(3):
                point = RowingDataPoint(
                    stroke_duration_secs=2.0,
                    stroke_distance_m=9.0,
                    time_500m_secs=140,
                    strokes_per_min=22,
                    power_watts=150 + i,
                    calories_per_hour=700,
                    resistance_level=8,
                )
                session.add_point(point)

            # Partial save
            session.partial_save(from_index=0)

            # Verify file was created with schema version
            parquet_file = pq.ParquetFile(session.filename)
            metadata = parquet_file.schema_arrow.metadata or {}
            schema_version_str = metadata.get(b"schema_version", b"").decode("utf-8")

            assert schema_version_str == str(SCHEMA_VERSION)

    def test_load_session_validates_schema_version(self):
        """load_session() should accept files with matching schema version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            session = RowingSession(session_start=datetime(2025, 1, 20, 10, 30, 0), data_dir=tmpdir)

            # Add a data point
            point = RowingDataPoint(
                stroke_duration_secs=2.0,
                stroke_distance_m=9.0,
                time_500m_secs=140,
                strokes_per_min=22,
                power_watts=150,
                calories_per_hour=700,
                resistance_level=8,
            )
            session.add_point(point)

            # Save and load
            session.save()
            df = RowingSession.load_session(session.filename)

            # Should succeed without raising ValueError
            assert df is not None
            assert len(df) == 1

    def test_load_session_rejects_mismatched_schema_version(self):
        """load_session() should reject files with mismatched schema version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with wrong schema version
            filepath = Path(tmpdir) / "test_session.parquet"

            # Create table with wrong schema version
            data = {
                "stroke_duration_secs": [2.0],
                "stroke_distance_m": [9.0],
                "time_500m_secs": [140],
                "strokes_per_min": [22],
                "power_watts": [150],
                "calories_per_hour": [700],
                "resistance_level": [8],
            }
            table = pa.table(data)
            # Add wrong schema version
            table = table.replace_schema_metadata({b"schema_version": b"999"})
            pq.write_table(table, filepath)

            # Should raise ValueError when loading
            with pytest.raises(ValueError, match="Schema version mismatch"):
                RowingSession.load_session(filepath)

    def test_load_session_handles_missing_schema_version(self):
        """load_session() should handle files without schema version metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file without schema version metadata (legacy file)
            filepath = Path(tmpdir) / "legacy_session.parquet"

            # Create table without schema version
            data = {
                "stroke_duration_secs": [2.0],
                "stroke_distance_m": [9.0],
                "time_500m_secs": [140],
                "strokes_per_min": [22],
                "power_watts": [150],
                "calories_per_hour": [700],
                "resistance_level": [8],
            }
            table = pa.table(data)
            # Don't add schema version metadata
            pq.write_table(table, filepath)

            # Should load successfully, defaulting to version 1
            loaded_df = RowingSession.load_session(filepath)
            assert loaded_df is not None
            assert len(loaded_df) == 1
