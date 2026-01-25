"""Tests for data migration framework."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest
import pyarrow as pa
import pyarrow.parquet as pq

from fluid_rower_monitor.migrations import (
    Migration,
    register_migration,
    get_migration_path,
    apply_migrations,
    list_migrations,
    MIGRATION_REGISTRY,
)
from fluid_rower_monitor.rowing_data import RowingSession, RowingDataPoint, SCHEMA_VERSION


class TestMigrationRegistry:
    """Test migration registration and discovery."""

    def test_register_migration_decorator(self):
        """register_migration should add migration to registry."""
        # Clear any existing migrations for this test
        test_key = (99, 100)
        if test_key in MIGRATION_REGISTRY:
            del MIGRATION_REGISTRY[test_key]

        @register_migration(99, 100, "Test migration")
        def test_migrate(df):
            return df

        assert test_key in MIGRATION_REGISTRY
        migration = MIGRATION_REGISTRY[test_key]
        assert migration.from_version == 99
        assert migration.to_version == 100
        assert migration.description == "Test migration"
        assert migration.func == test_migrate

        # Cleanup
        del MIGRATION_REGISTRY[test_key]

    def test_register_migration_without_description(self):
        """register_migration should generate default description."""
        test_key = (98, 99)
        if test_key in MIGRATION_REGISTRY:
            del MIGRATION_REGISTRY[test_key]

        @register_migration(98, 99)
        def test_migrate(df):
            return df

        migration = MIGRATION_REGISTRY[test_key]
        assert migration.description == "Migrate from schema v98 to v99"

        # Cleanup
        del MIGRATION_REGISTRY[test_key]

    def test_list_migrations(self):
        """list_migrations should return all registered migrations."""
        # Register test migrations
        test_keys = [(95, 96), (96, 97)]
        for from_v, to_v in test_keys:
            if (from_v, to_v) in MIGRATION_REGISTRY:
                del MIGRATION_REGISTRY[(from_v, to_v)]

        @register_migration(95, 96)
        def migrate_95_96(df):
            return df

        @register_migration(96, 97)
        def migrate_96_97(df):
            return df

        migrations = list_migrations()
        # Should include at least our test migrations
        versions = [(m.from_version, m.to_version) for m in migrations]
        assert (95, 96) in versions
        assert (96, 97) in versions

        # Cleanup
        for key in test_keys:
            del MIGRATION_REGISTRY[key]


class TestMigrationPath:
    """Test migration path discovery."""

    def test_get_migration_path_same_version(self):
        """get_migration_path should return empty list for same version."""
        path = get_migration_path(1, 1)
        assert path == []

    def test_get_migration_path_single_step(self):
        """get_migration_path should find single step migration."""
        test_key = (90, 91)
        if test_key in MIGRATION_REGISTRY:
            del MIGRATION_REGISTRY[test_key]

        @register_migration(90, 91)
        def migrate_90_91(df):
            return df

        path = get_migration_path(90, 91)
        assert len(path) == 1
        assert path[0].from_version == 90
        assert path[0].to_version == 91

        # Cleanup
        del MIGRATION_REGISTRY[test_key]

    def test_get_migration_path_multi_step(self):
        """get_migration_path should find multi-step migration path."""
        test_keys = [(80, 81), (81, 82), (82, 83)]
        for from_v, to_v in test_keys:
            if (from_v, to_v) in MIGRATION_REGISTRY:
                del MIGRATION_REGISTRY[(from_v, to_v)]

        @register_migration(80, 81)
        def migrate_80_81(df):
            return df

        @register_migration(81, 82)
        def migrate_81_82(df):
            return df

        @register_migration(82, 83)
        def migrate_82_83(df):
            return df

        path = get_migration_path(80, 83)
        assert len(path) == 3
        assert path[0].from_version == 80
        assert path[1].from_version == 81
        assert path[2].from_version == 82

        # Cleanup
        for key in test_keys:
            del MIGRATION_REGISTRY[key]

    def test_get_migration_path_missing_step(self):
        """get_migration_path should raise error if migration missing."""
        # Ensure migration doesn't exist
        if (70, 71) in MIGRATION_REGISTRY:
            del MIGRATION_REGISTRY[(70, 71)]

        with pytest.raises(ValueError, match="No migration found"):
            get_migration_path(70, 71)

    def test_get_migration_path_downgrade_not_supported(self):
        """get_migration_path should reject downgrade requests."""
        with pytest.raises(ValueError, match="Cannot downgrade"):
            get_migration_path(5, 3)


class TestApplyMigrations:
    """Test migration application."""

    def test_apply_migrations_no_change(self):
        """apply_migrations should return unchanged df for same version."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        result = apply_migrations(df, 1, 1)
        pd.testing.assert_frame_equal(result, df)

    def test_apply_migrations_single_step(self):
        """apply_migrations should apply single migration."""
        test_key = (60, 61)
        if test_key in MIGRATION_REGISTRY:
            del MIGRATION_REGISTRY[test_key]

        @register_migration(60, 61, "Add column b")
        def migrate_60_61(df):
            df["b"] = df["a"] * 2
            return df

        df = pd.DataFrame({"a": [1, 2, 3]})
        result = apply_migrations(df, 60, 61)

        assert "b" in result.columns
        assert list(result["b"]) == [2, 4, 6]
        # Original df should be unchanged
        assert "b" not in df.columns

        # Cleanup
        del MIGRATION_REGISTRY[test_key]

    def test_apply_migrations_multi_step(self):
        """apply_migrations should apply multiple migrations in sequence."""
        test_keys = [(50, 51), (51, 52)]
        for from_v, to_v in test_keys:
            if (from_v, to_v) in MIGRATION_REGISTRY:
                del MIGRATION_REGISTRY[(from_v, to_v)]

        @register_migration(50, 51, "Add column b")
        def migrate_50_51(df):
            df["b"] = df["a"] + 10
            return df

        @register_migration(51, 52, "Add column c")
        def migrate_51_52(df):
            df["c"] = df["a"] + df["b"]
            return df

        df = pd.DataFrame({"a": [1, 2, 3]})
        result = apply_migrations(df, 50, 52)

        assert "b" in result.columns
        assert "c" in result.columns
        assert list(result["b"]) == [11, 12, 13]
        assert list(result["c"]) == [12, 14, 16]  # a + b

        # Cleanup
        for key in test_keys:
            del MIGRATION_REGISTRY[key]

    def test_apply_migrations_handles_errors(self):
        """apply_migrations should raise clear error on migration failure."""
        test_key = (40, 41)
        if test_key in MIGRATION_REGISTRY:
            del MIGRATION_REGISTRY[test_key]

        @register_migration(40, 41)
        def failing_migrate(df):
            raise RuntimeError("Intentional failure")

        df = pd.DataFrame({"a": [1, 2, 3]})
        with pytest.raises(ValueError, match="Migration from v40 to v41 failed"):
            apply_migrations(df, 40, 41)

        # Cleanup
        del MIGRATION_REGISTRY[test_key]


class TestMigrationIntegration:
    """Test integration of migrations with RowingSession."""

    def test_load_session_with_current_version(self):
        """load_session should work normally with current schema version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create session with current schema
            session = RowingSession(data_dir=tmpdir)
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
            session.save()

            # Load should succeed without migration
            df = RowingSession.load_session(session.filename)
            assert len(df) == 1
            assert df["power_watts"][0] == 150

    def test_load_session_auto_migrate_disabled(self):
        """load_session should raise error when auto_migrate=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with old schema version
            filepath = Path(tmpdir) / "old_version.parquet"
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
            # Set to older version
            old_version = max(1, SCHEMA_VERSION - 1)
            if old_version == SCHEMA_VERSION:
                # If current version is 1, use version 0 for test
                old_version = 0
            table = table.replace_schema_metadata({b"schema_version": str(old_version).encode()})
            pq.write_table(table, filepath)

            # Should raise error when auto_migrate=False
            with pytest.raises(ValueError, match="Schema version mismatch"):
                RowingSession.load_session(filepath, auto_migrate=False)

    def test_load_session_newer_version_error(self):
        """load_session should error on newer schema version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "future_version.parquet"
            data = {"some_column": [1, 2, 3]}
            table = pa.table(data)
            # Set to future version
            future_version = SCHEMA_VERSION + 10
            table = table.replace_schema_metadata({b"schema_version": str(future_version).encode()})
            pq.write_table(table, filepath)

            # Should raise error about newer version
            with pytest.raises(ValueError, match="newer than current code"):
                RowingSession.load_session(filepath)


class TestMigrationDataclass:
    """Test Migration dataclass functionality."""

    def test_migration_apply(self):
        """Migration.apply should execute the migration function."""

        def add_column(df):
            df["new_col"] = 42
            return df

        migration = Migration(from_version=1, to_version=2, func=add_column, description="Add column")

        df = pd.DataFrame({"a": [1, 2, 3]})
        result = migration.apply(df)

        assert "new_col" in result.columns
        assert all(result["new_col"] == 42)
