from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from core.layout import LayoutSlot


# ---------- UI Component Registry (per-slot) ----------

@dataclass(frozen=True)
class ComponentSpec:
    slot_key: str             # stable python key (e.g. "home.header")
    component_id: str         # unique key
    order: int                # sorting order
    factory: Callable[[Any], Any]  # (ctx) -> Kivy widget instance


_COMPONENTS: Dict[str, List[ComponentSpec]] = {}


def ui_component(*, slot: LayoutSlot, component_id: str, order: int = 100):
    """Decorator to register UI components for a layout slot.

    The screen layout is referenced via python (LayoutSlot), not via hardcoded strings.
    """

    def decorator(factory: Callable[[Any], Any]) -> Callable[[Any], Any]:
        spec = ComponentSpec(slot_key=slot.key, component_id=component_id, order=order, factory=factory)
        _COMPONENTS.setdefault(slot.key, []).append(spec)
        return factory

    return decorator


def get_components(slot_key: str) -> List[ComponentSpec]:
    items = _COMPONENTS.get(slot_key, [])
    return sorted(items, key=lambda s: (s.order, s.component_id))


# ---------- UI Actions Registry (event handlers) ----------

@dataclass(frozen=True)
class ActionSpec:
    action_id: str
    handler: Callable[[Any], None]  # (ctx) -> None


_ACTIONS: Dict[str, ActionSpec] = {}


def ui_action(*, action_id: str):
    def decorator(fn: Callable[[Any], None]) -> Callable[[Any], None]:
        _ACTIONS[action_id] = ActionSpec(action_id=action_id, handler=fn)
        return fn

    return decorator


def get_action(action_id: str) -> Optional[ActionSpec]:
    return _ACTIONS.get(action_id)
