from __future__ import annotations

from typing import Any, Dict, List

from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import Screen


class BaseScreen(Screen):
    """Base class for all screens.

    Provides:
    - controller + screen_manager binding
    - go() navigation
    - do() action dispatch
    - mount_container() for slot-based UI mounting
    """

    controller = ObjectProperty(None)
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mounted: Dict[str, List[Any]] = {}

    def set_nav(self, sm, controller) -> None:
        self.screen_manager = sm
        self.controller = controller

    def go(self, screen_name: str) -> None:
        if not self.screen_manager:
            raise RuntimeError("ScreenManager not set on screen.")
        self.screen_manager.current = screen_name

    def do(self, action_id: str) -> None:
        if not self.controller:
            raise RuntimeError("Controller not set on screen.")
        self.controller.run_action(self, action_id)

    def mount_container(self, kv_id: str, widgets: List[Any]) -> None:
        """Mount widgets into a KV container by its id."""
        host = self.ids.get(kv_id)
        if host is None:
            raise RuntimeError(
                f"KV container id '{kv_id}' not found on screen '{self.name}'. "
                f"Check the .kv file ids."
            )

        host.clear_widgets()
        for w in widgets:
            host.add_widget(w)

        self._mounted[kv_id] = list(widgets)

    def get_container_widgets(self, kv_id: str) -> List[Any]:
        return list(self._mounted.get(kv_id, []))