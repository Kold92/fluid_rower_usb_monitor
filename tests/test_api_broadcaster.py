import asyncio

import anyio
import pytest

from fluid_rower_monitor.api.broadcaster import DataBroadcaster
from fluid_rower_monitor.rowing_data import RowingDataPoint


@pytest.mark.anyio
async def test_publish_and_subscribe():
    broadcaster = DataBroadcaster(mode="dev")
    point = RowingDataPoint(
        stroke_duration_secs=2.0,
        stroke_distance_m=9.0,
        time_500m_secs=150,
        strokes_per_min=24,
        power_watts=180,
        calories_per_hour=700,
        resistance_level=8,
    )

    received = []

    async def subscriber():
        async for p in broadcaster.subscribe():
            received.append(p)
            break

    async def wait_for_subscriber():
        for _ in range(50):
            if len(broadcaster.subscribers) > 0:
                return
            await anyio.sleep(0.01)

    async with anyio.create_task_group() as tg:
        tg.start_soon(subscriber)
        await wait_for_subscriber()
        await broadcaster._publish(point)
        tg.cancel_scope.cancel()

    assert received and received[0] == point


@pytest.mark.anyio
async def test_run_stream_selects_mode(monkeypatch):
    broadcaster = DataBroadcaster(mode="dev")
    flags = {"dev": False, "prod": False}

    async def fake_dev():
        flags["dev"] = True

    async def fake_prod():
        flags["prod"] = True

    monkeypatch.setattr(broadcaster, "_run_dev_stream", fake_dev)
    monkeypatch.setattr(broadcaster, "_run_production_stream", fake_prod)

    await broadcaster._run_stream()
    assert flags["dev"] is True
    assert flags["prod"] is False


@pytest.mark.anyio
async def test_run_dev_stream_emits_once(monkeypatch):
    broadcaster = DataBroadcaster(mode="dev")
    called = []

    async def fake_publish(point):
        called.append(point)
        raise asyncio.CancelledError()

    monkeypatch.setattr(broadcaster, "_publish", fake_publish)

    with pytest.raises(asyncio.CancelledError):
        await broadcaster._run_dev_stream()

    assert len(called) == 1


def test_read_serial_blocking_without_conn_returns_none():
    broadcaster = DataBroadcaster(mode="dev")
    assert broadcaster._read_serial_blocking() is None


@pytest.mark.anyio
async def test_run_production_stream_connection_failure(monkeypatch):
    broadcaster = DataBroadcaster(mode="production")

    class DummySerial:
        is_open = False

    monkeypatch.setattr("fluid_rower_monitor.api.broadcaster.setup_serial", lambda *a, **k: DummySerial())
    monkeypatch.setattr("fluid_rower_monitor.api.broadcaster.connect_to_device", lambda *a, **k: False)

    await broadcaster._run_production_stream()
