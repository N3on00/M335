from __future__ import annotations

import os
from kivy.lang import Builder

from ui.layouts.map_layout import MapLayout
from ui.screens.base_screen import BaseScreen

_KV_PATH = os.path.join(os.path.dirname(__file__), "map_screen.kv")
Builder.load_file(_KV_PATH)


class MapScreen(BaseScreen):
    layout_slots = [MapLayout.HEADER, MapLayout.MAIN]

    def on_pre_enter(self, *args):
        out = super().on_pre_enter(*args)
        if self.controller:
            self.do("map.reload")
        return out

    def after_build(self) -> None:
        pass
