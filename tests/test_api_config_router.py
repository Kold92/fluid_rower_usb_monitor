from pathlib import Path

from fluid_rower_monitor.api.routers import config as config_router
from fluid_rower_monitor.api.models import Config
from fluid_rower_monitor.settings import AppSettings


def test_get_config_uses_settings(monkeypatch):
    def fake_load_settings():
        settings = AppSettings()
        settings.ui.max_points = 42
        return settings

    monkeypatch.setattr(config_router, "load_settings", fake_load_settings)
    cfg = config_router.get_config()
    assert cfg.ui.max_points == 42


def test_update_config_writes_yaml(tmp_path, monkeypatch):
    cfg_path = tmp_path / "config.yaml"
    monkeypatch.setattr(config_router, "DEFAULT_CONFIG_PATH", str(cfg_path))

    cfg = Config()
    result = config_router.update_config(cfg)
    assert result.version == cfg.version
    assert Path(cfg_path).exists()
