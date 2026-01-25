"""Tests for application settings loading from YAML and env overrides."""

from fluid_rower_monitor.settings import AppSettings, load_settings


def test_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setenv("FRM_CONFIG_FILE", str(tmp_path / "missing.yaml"))

    settings = AppSettings()

    assert settings.serial.port == "/dev/ttyUSB0"
    assert settings.data.dir == "rowing_sessions"
    assert settings.logging.level == "INFO"
    assert settings.reconnect.max_attempts == 5


def test_load_from_yaml(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("""
version: 1
serial:
  port: /dev/ttyUSB1
  baudrate: 115200
  timeout_secs: 1.5
data:
  dir: custom_dir
logging:
  level: DEBUG
reconnect:
  max_attempts: 3
  backoff_secs: 0.25
""".strip())
    monkeypatch.setenv("FRM_CONFIG_FILE", str(cfg))

    settings = AppSettings()

    assert settings.serial.port == "/dev/ttyUSB1"
    assert settings.serial.baudrate == 115200
    assert settings.serial.timeout_secs == 1.5
    assert settings.data.dir == "custom_dir"
    assert settings.logging.level == "DEBUG"
    assert settings.reconnect.max_attempts == 3
    assert settings.reconnect.backoff_secs == 0.25


def test_env_overrides_yaml(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("version: 1\nserial:\n  port: /dev/ttyUSB1\n")
    monkeypatch.setenv("FRM_CONFIG_FILE", str(cfg))
    monkeypatch.setenv("FRM_SERIAL__PORT", "/dev/ttyUSB2")
    monkeypatch.setenv("FRM_SERIAL__TIMEOUT_SECS", "3.0")

    settings = AppSettings()

    assert settings.serial.port == "/dev/ttyUSB2"
    assert settings.serial.timeout_secs == 3.0


def test_load_settings_helper(tmp_path):
    cfg = tmp_path / "app.yaml"
    cfg.write_text("version: 1\ndata:\n  dir: alt_dir\n")

    settings = load_settings(cfg)

    assert settings.data.dir == "alt_dir"
    # Defaults still apply for missing fields
    assert settings.serial.baudrate == 9600
