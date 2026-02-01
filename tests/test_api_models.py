from datetime import datetime

from fluid_rower_monitor.api.models import ActiveSession, Config, LiveSample, LiveStats
from fluid_rower_monitor.settings import AppSettings


def test_config_from_app_settings():
    settings = AppSettings()
    cfg = Config.from_app_settings(settings)
    assert cfg.serial.port == settings.serial.port
    assert cfg.data.dir == settings.data.dir
    assert cfg.ui.x_axis_type == settings.ui.x_axis_type


def test_live_models_instantiation():
    sample = LiveSample(
        stroke_duration_secs=2.2,
        stroke_distance_m=9.5,
        cumulative_duration_secs=12.0,
        cumulative_distance_m=55.0,
        time_500m_secs=150,
        strokes_per_min=24,
        power_watts=180,
        calories_per_hour=700,
        resistance_level=8,
    )
    assert sample.cumulative_distance_m == 55.0

    stats = LiveStats(
        num_strokes=3,
        total_distance_m=55.0,
        total_duration_secs=12.0,
        avg_watts=170.0,
        max_watts=200,
        min_watts=120,
        avg_time_500m_secs=148.0,
        avg_strokes_per_min=24.0,
        max_strokes_per_min=26,
        total_calories=3.2,
        avg_resistance=8.0,
    )
    assert stats.total_distance_m == 55.0

    session = ActiveSession(id="abc", start=datetime.now(), is_active=True)
    assert session.is_active is True
