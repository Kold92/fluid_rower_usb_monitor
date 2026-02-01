from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter

from ..models import Config
from ..models import ErrorResponse
from ...settings import load_settings, ensure_config_exists, DEFAULT_CONFIG_PATH

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/", response_model=Config)
def get_config() -> Config:
    settings = load_settings()
    return Config.from_app_settings(settings)


@router.put("/", response_model=Config, responses={400: {"model": ErrorResponse}})
def update_config(cfg: Config) -> Config:
    """Persist full config to YAML.

    Partial updates can be added later; for now require full body.
    """
    path = ensure_config_exists(DEFAULT_CONFIG_PATH)
    data: dict[str, Any] = cfg.model_dump(mode="python")
    # pydantic models are nested; yaml can serialize dicts fine
    with Path(path).open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)
    return cfg
