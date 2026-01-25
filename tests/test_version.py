"""Tests for application version."""

import re
from fluid_rower_monitor import __version__


def test_version_exists():
    """Version attribute should exist."""
    assert __version__ is not None


def test_version_format():
    """Version should follow semantic versioning."""
    # Check for semantic versioning format: MAJOR.MINOR.PATCH
    pattern = r"^\d+\.\d+\.\d+$"
    assert re.match(pattern, __version__), f"Version '{__version__}' doesn't follow semver format"


def test_version_matches_pyproject():
    """Version in __init__ should match pyproject.toml."""
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        import tomli as tomllib  # Fallback for Python <3.11

    from pathlib import Path

    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    pyproject_version = pyproject["project"]["version"]
    assert __version__ == pyproject_version, (
        f"Version mismatch: __init__.py has {__version__}, " f"pyproject.toml has {pyproject_version}"
    )
