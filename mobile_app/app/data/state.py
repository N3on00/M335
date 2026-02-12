from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class AppConfig:
    api_base_url: str = "http://127.0.0.1:8000"
    request_timeout_s: float = 5.0


@dataclass
class AppState:
    """Global app state (KISS).

    - config: backend connectivity
    - cache: small in-memory cache (counts, last-loaded stuff)
    - map_config: map view configuration (tiles are best-effort depending on mapview version)
    """

    config: AppConfig = field(default_factory=AppConfig)
    cache: Dict[str, Any] = field(default_factory=dict)

    # Keep this dict so MapConfig(**map_config) works.
    map_config: Dict[str, Any] = field(default_factory=lambda: {
        "default_lat": 47.3769,
        "default_lon": 8.5417,
        "default_zoom": 12,
        "tile_url": None,
        "tile_cache_key": None,
    })

    def load_from_file(self, path: str) -> None:
        if not os.path.exists(path):
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cfg = data.get("config", {})
        self.config = AppConfig(
            api_base_url=str(cfg.get("api_base_url", self.config.api_base_url)),
            request_timeout_s=float(cfg.get("request_timeout_s", self.config.request_timeout_s)),
        )

        mc = data.get("map_config", {})
        if isinstance(mc, dict):
            # Merge
            merged = dict(self.map_config)
            merged.update(mc)
            self.map_config = merged