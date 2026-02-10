from __future__ import annotations

from kivy.uix.screenmanager import ScreenManager

from ui.screens.home.home_screen import HomeScreen
from ui.screens.map.map_screen import MapScreen

class Navigation:
    def __init__(self):
        self._sm: ScreenManager | None = None

    def build_screen_manager(self, controller) -> ScreenManager:
        sm = ScreenManager()

        # Instantiate screens
        home = HomeScreen()
        map_ = MapScreen()

        # Attach to SM
        sm.add_widget(home)
        sm.add_widget(map_)

        # Let controller wire registries into screens
        controller.build_screen(home)
        controller.build_screen(map_)

        # Provide navigation helper to screens
        home.set_nav(sm, controller)
        map_.set_nav(sm, controller)

        sm.current = "home"
        self._sm = sm
        return sm

    def go(self, name: str) -> None:
        if not self._sm:
            return
        self._sm.current = name
