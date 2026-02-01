"""Dependency stubs (e.g., future auth hooks)."""

from fastapi import Depends


def noop_auth_dependency():  # pragma: no cover
    """Placeholder for future authentication; currently does nothing."""
    return True
