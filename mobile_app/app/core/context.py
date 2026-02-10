from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict

from data.state import AppState
from core.navigation import Navigation

@dataclass
class AppContext:
    state: AppState
    services: Dict[str, Any]
    nav: Navigation
