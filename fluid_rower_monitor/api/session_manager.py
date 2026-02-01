from __future__ import annotations

from datetime import datetime
from typing import Callable

from ..rowing_data import RowingDataPoint, RowingSession

_active_session: RowingSession | None = None
_device_reset_handler: Callable[[], None] | None = None


class DeviceResetError(RuntimeError):
    """Raised when the rower device reset fails."""


def get_active_session() -> RowingSession | None:
    return _active_session


def set_device_reset_handler(handler: Callable[[], None] | None) -> None:
    """Register a handler to reset the rower device on session start."""
    global _device_reset_handler
    _device_reset_handler = handler


def start_session() -> RowingSession:
    global _active_session
    if _active_session is not None:
        raise RuntimeError("Session already active")
    if _device_reset_handler is not None:
        try:
            _device_reset_handler()
        except Exception as exc:
            raise DeviceResetError(f"Device reset failed: {exc}") from exc
    _active_session = RowingSession(session_start=datetime.now())
    return _active_session


def stop_session() -> RowingSession:
    global _active_session
    if _active_session is None:
        raise RuntimeError("No active session to stop")
    session = _active_session
    session.save()
    _active_session = None
    return session


def record_point(point: RowingDataPoint) -> None:
    session = _active_session
    if session is None:
        return
    session.add_point(point)
