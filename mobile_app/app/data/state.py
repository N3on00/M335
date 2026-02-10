from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import json
from pathlib import Path

CONFIG_PATH = Path("app_config.json")

@dataclass
class AppConfig:
    api_base_url: str = "http://127.0.0.1:8000"
    request_timeout_s: float = 5.0

    @classmethod
    def load(cls) -> "AppConfig":
        if not CONFIG_PATH.exists():
            cfg = cls()
            CONFIG_PATH.write_text(json.dumps(cfg.__dict__, indent=2), encoding="utf-8")
            return cfg
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return cls(**data)

    def save(self) -> None:
        CONFIG_PATH.write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")

@dataclass
class AppState:
    config: AppConfig = field(default_factory=AppConfig.load)
    cache: Dict[str, Any] = field(default_factory=dict)
    last_error: Optional[str] = None
