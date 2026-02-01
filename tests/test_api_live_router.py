from fastapi import FastAPI
from fastapi.testclient import TestClient

from fluid_rower_monitor.api.routers.live import router as live_router
import fluid_rower_monitor.api.routers.live as live_module
from fluid_rower_monitor.rowing_data import RowingDataPoint, RowingSession


class DummyBroadcaster:
    def __init__(self, points):
        self._points = points

    async def subscribe(self):
        for point in self._points:
            yield point


def test_live_stream_emits_sample_and_stats(monkeypatch):
    points = [
        RowingDataPoint(
            stroke_duration_secs=2.0,
            stroke_distance_m=9.0,
            time_500m_secs=150,
            strokes_per_min=24,
            power_watts=180,
            calories_per_hour=700,
            resistance_level=8,
            cumulative_distance_m=9.0,
            cumulative_duration_secs=2.0,
        ),
        RowingDataPoint(
            stroke_duration_secs=2.2,
            stroke_distance_m=9.2,
            time_500m_secs=148,
            strokes_per_min=25,
            power_watts=190,
            calories_per_hour=710,
            resistance_level=8,
            cumulative_distance_m=18.2,
            cumulative_duration_secs=4.2,
        ),
    ]

    session = RowingSession()
    monkeypatch.setattr(live_module, "get_broadcaster", lambda: DummyBroadcaster(points))
    monkeypatch.setattr(live_module, "get_active_session", lambda: session)

    app = FastAPI()
    app.include_router(live_router)

    client = TestClient(app)
    with client.websocket_connect("/ws/live") as ws:
        msg1 = ws.receive_json()
        msg2 = ws.receive_json()
        msg3 = ws.receive_json()

    assert msg1["type"] == "session"
    assert msg2["type"] == "sample"
    assert msg3["type"] == "stats"
    assert msg3["data"]["total_distance_m"] == 9.0
    assert msg3["data"]["avg_time_500m_secs"] == 150.0
