from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import json

CONFIG_PATH = Path("app_config.json")


@dataclass
class AppConfig:
    # Backend (FastAPI)
    api_base_url: str = "http://127.0.0.1:8000"
    request_timeout_s: float = 5.0

    # Map defaults
    map_default_lat: float = 47.0
    map_default_lon: float = 9.0
    map_default_zoom: int = 12

    # Optional: custom tile provider (MapView). Leave empty to use OpenStreetMap.
    # Example (Google Map Tiles API) requires API key + billing:
    # https://tile.googleapis.com/v1/2dtiles/{z}/{x}/{y}?key=YOUR_KEY
    map_tile_url: str = ""
    map_tile_cache_key: str = "osm"

    @classmethod
    def load(cls) -> "AppConfig":
        if not CONFIG_PATH.exists():
            cfg = cls()
            cfg.save()
            return cfg

        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        # Forward compatible: ignore unknown keys, use defaults for missing keys
        known = {k: data.get(k, getattr(cls, k)) for k in cls.__annotations__.keys()}
        return cls(**known)

    def save(self) -> None:
        CONFIG_PATH.write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")


@dataclass
class AppState:
    config: AppConfig = field(default_factory=AppConfig.load)
    cache: Dict[str, Any] = field(default_factory=dict)
    last_error: Optional[str] = None
