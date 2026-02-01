"""Application settings using YAML + environment overrides.

Priority: env vars (FRM_ prefix, nested via __) > YAML file (FRM_CONFIG_FILE or ./config.yaml) > defaults.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CONFIG_PATH = "config.yaml"
EXAMPLE_CONFIG_PATH = "config.example.yaml"


class SerialSettings(BaseModel):
    port: str = Field("/dev/ttyUSB0", description="Serial port path")
    baudrate: int = Field(9600, description="Baud rate for serial communication")
    timeout_secs: float = Field(2.0, description="Read timeout in seconds")


class DataSettings(BaseModel):
    dir: str = Field("rowing_sessions", description="Directory for saved session files")


class LoggingSettings(BaseModel):
    level: str = Field("INFO", description="Log level (e.g., DEBUG, INFO, WARN)")


class ReconnectSettings(BaseModel):
    max_attempts: int = Field(5, ge=1, description="Max connection retry attempts")
    backoff_secs: float = Field(0.5, ge=0.0, description="Backoff between retries in seconds")
    flush_interval_secs: float = Field(60.0, ge=1.0, description="Periodic session flush interval in seconds")
    flush_after_strokes: int = Field(10, ge=1, description="Flush session after N strokes")


class UISettings(BaseModel):
    """UI configuration preferences."""

    x_axis_type: Literal["samples", "time", "distance"] = Field(
        default="samples",
        description=(
            "X-axis display mode for charts: samples (stroke number), time (elapsed seconds), "
            "distance (cumulative meters)"
        ),
    )
    max_points: int = Field(
        default=30, ge=10, le=500, description="Number of data points to display in charts (10-500)"
    )


class AppSettings(BaseSettings):
    """Validated application settings with YAML + env support."""

    version: int = Field(1, description="Config schema version")
    serial: SerialSettings = SerialSettings()
    data: DataSettings = DataSettings()
    logging: LoggingSettings = LoggingSettings()
    reconnect: ReconnectSettings = ReconnectSettings()
    ui: UISettings = UISettings()

    model_config = SettingsConfigDict(
        env_prefix="FRM_",
        env_nested_delimiter="__",
        extra="forbid",
    )

    @staticmethod
    def _yaml_config_settings_source() -> Dict[str, Any]:
        """Load settings from YAML if available (path from FRM_CONFIG_FILE or default)."""
        path_str = os.environ.get("FRM_CONFIG_FILE", DEFAULT_CONFIG_PATH)
        path = Path(path_str)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
            if not isinstance(data, dict):
                raise ValidationError.from_exception_data(
                    "AppSettings",
                    [
                        {
                            "loc": ("__root__",),
                            "msg": "Configuration root must be a mapping",
                            "type": "value_error",
                        }
                    ],
                )
            return data

    @classmethod
    def settings_customise_sources(
        cls, settings_cls, init_settings, env_settings, dotenv_settings, file_secret_settings
    ):
        # Priority: env > YAML file > init kwargs > .env / secrets
        return (
            env_settings,
            cls._yaml_config_settings_source,
            init_settings,
            dotenv_settings,
            file_secret_settings,
        )


def load_settings(config_path: str | Path | None = None) -> AppSettings:
    """Helper to load settings with an optional explicit YAML path."""
    if config_path is not None:
        os.environ["FRM_CONFIG_FILE"] = str(config_path)
    return AppSettings()


def ensure_config_exists(config_path: str | Path | None = None) -> Path:
    """Ensure config.yaml exists, creating it from config.example.yaml if needed.

    Args:
        config_path: Optional explicit config path. If None, uses DEFAULT_CONFIG_PATH.

    Returns:
        Path to the config file (existing or newly created).

    Raises:
        FileNotFoundError: If config.example.yaml is missing when needed.
    """
    target = Path(config_path) if config_path else Path(DEFAULT_CONFIG_PATH)

    if target.exists():
        return target

    # Config doesn't exist, try to copy from example
    example = Path(EXAMPLE_CONFIG_PATH)
    if not example.exists():
        raise FileNotFoundError(
            f"Config file '{target}' not found and example file '{example}' is missing. "
            "Cannot generate default configuration."
        )

    shutil.copy(example, target)
    return target
