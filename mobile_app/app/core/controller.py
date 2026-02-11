from __future__ import annotations

from dataclasses import dataclass

from core.context import AppContext
from core.registry import get_action, get_components
from ui.screens.base_screen import BaseScreen


@dataclass(frozen=True)
class ActionContext:
    """Context passed to ui_action handlers."""
    app: AppContext
    screen: BaseScreen


class UIController:
    def __init__(self, ctx: AppContext):
        self._ctx = ctx

    def build_screen(self, screen: BaseScreen) -> None:
        # Defensive: ensure controller is set
        if screen.controller is None:
            screen.controller = self

        # Build all registered containers for this screen
        for slot in getattr(screen, "layout_slots", []):
            specs = get_components(slot.key)
            ctx = ActionContext(app=self._ctx, screen=screen)
            widgets = [spec.factory(ctx) for spec in specs]

            # slot.kv_id is the Kivy id of the container
            screen.mount_container(slot.kv_id, widgets)

        # Call hook after mounting widgets
        if hasattr(screen, "after_build"):
            screen.after_build()

    def run_action(self, screen: BaseScreen, action_id: str) -> None:
        spec = get_action(action_id)
        if not spec:
            raise RuntimeError(f"Unknown action_id: {action_id}")

        ctx = ActionContext(app=self._ctx, screen=screen)
        spec.handler(ctx)