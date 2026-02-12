from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kivy.factory import Factory

from data.state import AppState


@dataclass(frozen=True)
class AppContext:
    """App-wide context.

    Keep existing constructor args (state, nav) to avoid breaking app/app.py.
    Add kv_factory() for reusable KV templates (DRY).
    """
    state: AppState
    nav: Any

    def kv_factory(self, name: str):
        # Example: ctx.app.kv_factory("RoundedCard")()
        return getattr(Factory, name)