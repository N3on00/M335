from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class AppConfig:
    api_base_url: str = "http://127.0.0.1:8000"
    request_timeout_s: float = 5.0
    support_email: str = "support@spotonsight.app"


@dataclass
class AppState:
    """Global app state (KISS).

    - config: backend connectivity
    - cache: small in-memory cache (counts, last-loaded stuff)
    - map_config: map view configuration (tiles are best-effort depending on mapview version)
    """

    config: AppConfig = field(default_factory=AppConfig)
    cache: Dict[str, Any] = field(default_factory=dict)
    auth_token: Optional[str] = None
    current_user: Optional[Dict[str, Any]] = None

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

        cfg = data.get("config", data) if isinstance(data, dict) else {}
        self.config = AppConfig(
            api_base_url=str(cfg.get("api_base_url", self.config.api_base_url)),
            request_timeout_s=float(cfg.get("request_timeout_s", self.config.request_timeout_s)),
            support_email=str(cfg.get("support_email", self.config.support_email)),
        )

        mc = data.get("map_config", {})
        if isinstance(mc, dict):
            # Merge
            merged = dict(self.map_config)
            merged.update(mc)
            self.map_config = merged

    def load_session(self, path: str) -> None:
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return

        token = data.get("auth_token")
        user = data.get("current_user")

        if isinstance(token, str) and token.strip():
            self.auth_token = token.strip()
        else:
            self.auth_token = None

        self.current_user = dict(user) if isinstance(user, dict) else None

    def save_session(self, path: str) -> None:
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        data = {
            "auth_token": self.auth_token,
            "current_user": self.current_user,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
