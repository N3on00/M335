from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from core.context import AppContext
from core.registry import get_components, get_action

@dataclass
class UIActionContext:
    app: AppContext
    screen: Any  # current screen instance

class UIController:
    """Generic controller that wires views from registries.

    Rule: Views define containers by `container_id` and offer `mount_container(container_id, widgets)`.
    Controller never needs edits when adding new buttons/widgets: you only add decorators.
    """

    def __init__(self, app_ctx: AppContext):
        self.app_ctx = app_ctx

    def build_screen(self, screen: Any) -> None:
        """Called by Navigation once a screen is instantiated."""
        # Wire UI components into screen containers
        for container_id in screen.container_ids:
            specs = get_components(container_id)
            widgets = [spec.factory(self.app_ctx) for spec in specs]
            screen.mount_container(container_id, widgets)

        # Let screen do final per-screen initialization if it wants
        if hasattr(screen, "after_build"):
            screen.after_build()

    def run_action(self, screen: Any, action_id: str) -> None:
        spec = get_action(action_id)
        if not spec:
            raise RuntimeError(f"Unknown action_id: {action_id}")
        spec.handler(UIActionContext(app=self.app_ctx, screen=screen))
