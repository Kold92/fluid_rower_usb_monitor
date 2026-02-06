from fluid_rower_monitor.api.routers import sessions as sessions_router
import fluid_rower_monitor.api.routers.sessions as sessions_module
from fluid_rower_monitor.rowing_data import RowingSession
from fluid_rower_monitor.rowing_data import SessionStats


def test_list_sessions(monkeypatch, tmp_path):
    fake_file = tmp_path / "2026-01-01_10-00-00.parquet"
    fake_file.touch()

    monkeypatch.setattr(RowingSession, "list_sessions", lambda data_dir="rowing_sessions": [fake_file])
    sessions = sessions_router.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == fake_file.name


def test_get_active_none():
    assert sessions_router.get_active() is None


def test_start_and_stop_session():
    session = sessions_router.start()
    assert session.is_active is True
    summary = sessions_router.stop()
    assert summary.id.endswith(".parquet")


def test_get_session_details(monkeypatch, tmp_path):
    fake_file = tmp_path / "2026-01-01_10-00-00.parquet"
    fake_file.touch()

    monkeypatch.setattr(RowingSession, "list_sessions", lambda data_dir="rowing_sessions": [fake_file])
    monkeypatch.setattr(
        sessions_module.RowingAnalyzer,
        "get_historical_stats",
        lambda fp: SessionStats(
            num_strokes=10,
            total_distance_m=1000.0,
            total_duration_secs=300.0,
            mean_time_500m_secs=150.0,
            min_time_500m_secs=140,
            max_time_500m_secs=160,
            mean_strokes_per_min=24.0,
            max_strokes_per_min=28,
            mean_power_watts=180.0,
            max_power_watts=220,
            min_power_watts=140,
            total_calories=600,
            mean_resistance=8.0,
        ),
    )

    detail = sessions_router.get_session(fake_file.name)
    assert detail.id == fake_file.name
    assert detail.stats is not None
