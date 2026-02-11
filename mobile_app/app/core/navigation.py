from __future__ import annotations

from kivy.uix.screenmanager import ScreenManager

from ui.screens.home.home_screen import HomeScreen
from ui.screens.map.map_screen import MapScreen


class Navigation:
    def __init__(self):
        self.screen_manager: ScreenManager | None = None

    def build_screen_manager(self, controller) -> ScreenManager:
        sm = ScreenManager()
        self.screen_manager = sm

        # Instantiate screens
        home = HomeScreen(name="home")
        map_ = MapScreen(name="map")

        # Add screens first
        sm.add_widget(home)
        sm.add_widget(map_)

        # IMPORTANT: set controller/sm on screen BEFORE building UI (after_build may call actions)
        for screen in (home, map_):
            screen.set_nav(sm, controller)
            controller.build_screen(screen)

        sm.current = "home"
        return sm