from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, status

from ..models import ActiveSession, SessionSummary, SessionDetail
from ..session_manager import DeviceResetError, get_active_session, start_session, stop_session
from ...rowing_analyzer import RowingAnalyzer
from ...rowing_data import RowingSession  # type: ignore

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _parse_start_from_filename(path: Path) -> datetime | None:
    try:
        # Filename format: YYYY-MM-DD_HH-MM-SS.parquet
        name = path.stem
        return datetime.strptime(name, "%Y-%m-%d_%H-%M-%S")
    except Exception:
        return None


def _to_plain_value(value: Any) -> Any:
    """Convert numpy scalar types to plain Python values for JSON serialization."""
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value
    return value


@router.get("/", response_model=List[SessionSummary])
def list_sessions() -> List[SessionSummary]:
    files = RowingSession.list_sessions()
    summaries: List[SessionSummary] = []
    for f in files:
        summaries.append(
            SessionSummary(
                id=f.name,
                start=_parse_start_from_filename(f),
                # num_strokes and totals can be added later (quick metadata cache)
            )
        )
    return summaries


@router.get("/active", response_model=ActiveSession | None)
def get_active() -> ActiveSession | None:
    session = get_active_session()
    if session is None:
        return None
    return ActiveSession(id=session.filename.name, start=session.session_start, is_active=True)


@router.post("/start", response_model=ActiveSession, status_code=status.HTTP_201_CREATED)
def start() -> ActiveSession:
    try:
        session = start_session()
    except DeviceResetError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return ActiveSession(id=session.filename.name, start=session.session_start, is_active=True)


@router.post("/stop", response_model=SessionSummary)
def stop() -> SessionSummary:
    try:
        session = stop_session()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return SessionSummary(id=session.filename.name, start=session.session_start)


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: str) -> SessionDetail:
    # Security note: sanitize path traversal; limit to data dir
    files = RowingSession.list_sessions()
    match = [f for f in files if f.name == session_id]
    if not match:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    fp = match[0]
    # Compute session stats (total distance, pace, power, etc.)
    try:
        session_stats = RowingAnalyzer.get_historical_stats(fp)
        if session_stats:
            stats = {key: _to_plain_value(val) for key, val in asdict(session_stats).items()}
        else:
            stats = {}
    except Exception:
        stats = {}

    return SessionDetail(id=session_id, start=_parse_start_from_filename(fp), stats=stats)
