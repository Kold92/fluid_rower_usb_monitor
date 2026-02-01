import pytest

from fluid_rower_monitor.api.session_manager import (
    DeviceResetError,
    get_active_session,
    record_point,
    set_device_reset_handler,
    start_session,
    stop_session,
)
from fluid_rower_monitor.rowing_data import RowingDataPoint


def test_start_stop_session_with_reset_handler():
    called = []

    def handler():
        called.append(True)

    set_device_reset_handler(handler)
    session = start_session()
    assert session is not None
    assert called == [True]

    stopped = stop_session()
    assert stopped is not None
    assert get_active_session() is None
    set_device_reset_handler(None)


def test_start_session_reset_failure():
    def handler():
        raise RuntimeError("boom")

    set_device_reset_handler(handler)
    with pytest.raises(DeviceResetError):
        start_session()
    set_device_reset_handler(None)


def test_record_point_adds_to_session():
    session = start_session()
    point = RowingDataPoint(
        stroke_duration_secs=2.0,
        stroke_distance_m=9.0,
        time_500m_secs=150,
        strokes_per_min=24,
        power_watts=180,
        calories_per_hour=700,
        resistance_level=8,
    )
    record_point(point)
    assert len(session.data_points) == 1
    stop_session()
