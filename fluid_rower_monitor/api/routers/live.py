from __future__ import annotations

import asyncio
import json
from dataclasses import asdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..broadcaster import get_broadcaster
from ..models import ActiveSession, LiveSample, LiveStats
from ..session_manager import get_active_session

router = APIRouter(prefix="/ws", tags=["live"])


@router.websocket("/live")
async def live_stream(ws: WebSocket):
    await ws.accept()
    broadcaster = get_broadcaster()

    stroke_count = 0
    total_distance = 0.0
    total_duration = 0.0
    sum_watts = 0.0
    max_watts = 0
    min_watts = 9999
    sum_spm = 0.0
    max_spm = 0
    sum_time_500m = 0.0
    sum_calories = 0.0
    sum_resistance = 0.0
    last_session_id: str | None = None

    try:
        async for point in broadcaster.subscribe():
            active_session = get_active_session()
            active_session_id = active_session.filename.name if active_session else None
            if active_session_id and active_session_id != last_session_id:
                stroke_count = 0
                total_distance = 0.0
                total_duration = 0.0
                sum_watts = 0.0
                max_watts = 0
                min_watts = 9999
                sum_spm = 0.0
                max_spm = 0
                sum_time_500m = 0.0
                sum_calories = 0.0
                sum_resistance = 0.0
                last_session_id = active_session_id

                session_msg = ActiveSession(
                    id=active_session_id,
                    start=active_session.session_start,
                    is_active=True,
                )
                await ws.send_text(json.dumps({"type": "session", "data": session_msg.model_dump(mode="json")}))

            # Send sample
            sample = LiveSample(**asdict(point))
            await ws.send_text(json.dumps({"type": "sample", "data": sample.model_dump()}))

            # Update stats
            stroke_count += 1
            if point.cumulative_distance_m is not None:
                total_distance = point.cumulative_distance_m
            else:
                total_distance += point.stroke_distance_m

            if point.cumulative_duration_secs is not None:
                total_duration = point.cumulative_duration_secs
            else:
                total_duration += point.stroke_duration_secs
            sum_watts += point.power_watts
            max_watts = max(max_watts, point.power_watts)
            min_watts = min(min_watts, point.power_watts)
            sum_spm += point.strokes_per_min
            max_spm = max(max_spm, point.strokes_per_min)
            sum_time_500m += point.time_500m_secs
            sum_calories += point.calories_per_hour
            sum_resistance += point.resistance_level

            # Send stats after every stroke
            stats = LiveStats(
                num_strokes=stroke_count,
                total_distance_m=round(total_distance, 2),
                total_duration_secs=round(total_duration, 2),
                avg_watts=round(sum_watts / stroke_count, 1),
                max_watts=max_watts,
                min_watts=min_watts if min_watts != 9999 else 0,
                avg_time_500m_secs=round(sum_time_500m / stroke_count, 1),
                avg_strokes_per_min=round(sum_spm / stroke_count, 1),
                max_strokes_per_min=max_spm,
                total_calories=round(sum_calories / stroke_count * total_duration / 3600, 1),
                avg_resistance=round(sum_resistance / stroke_count, 1),
            )
            await ws.send_text(json.dumps({"type": "stats", "data": stats.model_dump()}))

    except WebSocketDisconnect:
        return
    except asyncio.CancelledError:
        return
