from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any, Dict, List, Optional

# ---------- UI Component Registry (per-container) ----------

@dataclass(frozen=True)
class ComponentSpec:
    container_id: str        # e.g. "home:main", "home:toolbar", "map:overlay"
    component_id: str        # unique key
    order: int               # sorting order
    factory: Callable[[Any], Any]  # (ctx) -> Kivy widget instance

_COMPONENTS: Dict[str, List[ComponentSpec]] = {}

def ui_component(*, container_id: str, component_id: str, order: int = 100):
    """Decorator to register UI components for a container."""
    def decorator(factory: Callable[[Any], Any]) -> Callable[[Any], Any]:
        spec = ComponentSpec(container_id=container_id, component_id=component_id, order=order, factory=factory)
        _COMPONENTS.setdefault(container_id, []).append(spec)
        return factory
    return decorator

def get_components(container_id: str) -> List[ComponentSpec]:
    items = _COMPONENTS.get(container_id, [])
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
