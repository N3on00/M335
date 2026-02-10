from __future__ import annotations

from typing import Dict, List, Any, Optional

from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty
from kivy.lang import Builder

class BaseScreen(Screen):
    """Base for all screens.

    - Defines `container_ids` (list[str])
    - Implements `mount_container(container_id, widgets)`
    - Holds references to ScreenManager + Controller for navigation/action dispatch
    """

    controller = ObjectProperty(None)
    screen_manager = ObjectProperty(None)

    # override in subclasses
    container_ids: List[str] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._container_widgets: Dict[str, List[Any]] = {}

    def set_nav(self, sm, controller) -> None:
        self.screen_manager = sm
        self.controller = controller

    def go(self, screen_name: str) -> None:
        if self.screen_manager:
            self.screen_manager.current = screen_name

    def do(self, action_id: str) -> None:
        if not self.controller:
            raise RuntimeError("Controller not set on screen.")
        self.controller.run_action(self, action_id)

    def mount_container(self, container_id: str, widgets: List[Any]) -> None:
        """Mounts widgets into a container.
        The container must exist as an `id:` in kv with the same name as container_id (sanitized).
        """
        host = self._find_container_widget(container_id)
        if host is None:
            raise RuntimeError(f"Container widget not found for container_id='{container_id}' in screen '{self.name}'")
        host.clear_widgets()
        for w in widgets:
            host.add_widget(w)
        self._container_widgets[container_id] = widgets

    def _find_container_widget(self, container_id: str):
        # Kivy ids cannot contain ":" reliably; we map ":" -> "__"
        kid = container_id.replace(":", "__")
        return self.ids.get(kid)
