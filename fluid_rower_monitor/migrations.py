"""Data migration framework for schema version upgrades.

This module provides a registry-based migration system for upgrading parquet files
from older schema versions to the current version.

Example usage:
    To add a new migration from v2 to v3:

    @register_migration(2, 3)
    def migrate_v2_to_v3(df: pd.DataFrame) -> pd.DataFrame:
        # Add new column with default value
        df['new_column'] = 0
        return df
"""

from dataclasses import dataclass
from typing import Callable, Dict, Tuple
import pandas as pd


@dataclass
class Migration:
    """Represents a migration from one schema version to another."""

    from_version: int
    to_version: int
    func: Callable[[pd.DataFrame], pd.DataFrame]
    description: str

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply this migration to a DataFrame."""
        return self.func(df)


# Migration registry: {(from_version, to_version): Migration}
MIGRATION_REGISTRY: Dict[Tuple[int, int], Migration] = {}


def register_migration(from_version: int, to_version: int, description: str = "") -> Callable:
    """
    Decorator to register a migration function.

    Args:
        from_version: Source schema version
        to_version: Target schema version
        description: Human-readable description of the migration

    Returns:
        Decorator function

    Example:
        @register_migration(1, 2, "Add session_type column")
        def migrate_v1_to_v2(df: pd.DataFrame) -> pd.DataFrame:
            df['session_type'] = 'rowing'
            return df
    """

    def decorator(func: Callable[[pd.DataFrame], pd.DataFrame]) -> Callable:
        migration = Migration(
            from_version=from_version,
            to_version=to_version,
            func=func,
            description=description or f"Migrate from schema v{from_version} to v{to_version}",
        )
        MIGRATION_REGISTRY[(from_version, to_version)] = migration
        return func

    return decorator


def get_migration_path(from_version: int, to_version: int) -> list[Migration]:
    """
    Find the sequence of migrations needed to upgrade from one version to another.

    Args:
        from_version: Current schema version
        to_version: Target schema version

    Returns:
        List of migrations in order to apply

    Raises:
        ValueError: If no migration path exists
    """
    if from_version == to_version:
        return []

    if from_version > to_version:
        raise ValueError(f"Cannot downgrade from v{from_version} to v{to_version}. " "Downgrades are not supported.")

    # Build migration path by stepping through versions
    path = []
    current_version = from_version

    while current_version < to_version:
        next_version = current_version + 1
        migration_key = (current_version, next_version)

        if migration_key not in MIGRATION_REGISTRY:
            raise ValueError(
                f"No migration found from v{current_version} to v{next_version}. "
                f"Cannot upgrade from v{from_version} to v{to_version}."
            )

        path.append(MIGRATION_REGISTRY[migration_key])
        current_version = next_version

    return path


def apply_migrations(df: pd.DataFrame, from_version: int, to_version: int) -> pd.DataFrame:
    """
    Apply all necessary migrations to upgrade a DataFrame to target version.

    Args:
        df: DataFrame to migrate
        from_version: Current schema version
        to_version: Target schema version

    Returns:
        Migrated DataFrame

    Raises:
        ValueError: If migration path doesn't exist or migration fails
    """
    migrations = get_migration_path(from_version, to_version)

    if not migrations:
        return df  # Already at target version

    print(f"Migrating data from schema v{from_version} to v{to_version} " f"({len(migrations)} step(s))")

    migrated_df = df.copy()
    for migration in migrations:
        print(f"  Applying: {migration.description}")
        try:
            migrated_df = migration.apply(migrated_df)
        except Exception as e:
            raise ValueError(
                f"Migration from v{migration.from_version} to " f"v{migration.to_version} failed: {e}"
            ) from e

    print(f"Migration complete: v{from_version} → v{to_version}")
    return migrated_df


def list_migrations() -> list[Migration]:
    """
    Get a list of all registered migrations.

    Returns:
        List of all migrations in the registry
    """
    return sorted(MIGRATION_REGISTRY.values(), key=lambda m: (m.from_version, m.to_version))


# Example migration (commented out - uncomment when needed):
# @register_migration(1, 2, "Add session_type column with default value")
# def migrate_v1_to_v2(df: pd.DataFrame) -> pd.DataFrame:
#     """Add session_type column to distinguish between different workout types."""
#     df['session_type'] = 'rowing'  # Default to rowing for all existing sessions
#     return df
