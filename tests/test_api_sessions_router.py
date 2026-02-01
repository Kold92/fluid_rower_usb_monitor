import pandas as pd

from fluid_rower_monitor.api.routers import sessions as sessions_router
from fluid_rower_monitor.rowing_data import RowingSession


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
    monkeypatch.setattr(RowingSession, "load_session", lambda fp: pd.DataFrame({"a": [1, 2, 3]}))

    detail = sessions_router.get_session(fake_file.name)
    assert detail.id == fake_file.name
    assert detail.stats is not None
