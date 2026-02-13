from __future__ import annotations

import os

from kivy.lang import Builder

from ui.layouts.home_layout import HomeLayout
from ui.screens.base_screen import BaseScreen


# Load KV rule for this screen (ensures ids like home_header exist on the HomeScreen instance)
_KV_PATH = os.path.join(os.path.dirname(__file__), "home_screen.kv")
Builder.load_file(_KV_PATH)


class HomeScreen(BaseScreen):
    """Home screen."""

    layout_slots = [HomeLayout.HEADER, HomeLayout.MAIN, HomeLayout.FOOTER]

    def on_pre_enter(self, *args):
        out = super().on_pre_enter(*args)
        if self.controller:
            self.controller.build_screen(self)
        return out

    def after_build(self) -> None:
        # Optional autoload
        # self.do("home.refresh")
        pass
