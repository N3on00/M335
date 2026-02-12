from __future__ import annotations

import os
from kivy.lang import Builder

from ui.layouts.map_layout import MapLayout
from ui.screens.base_screen import BaseScreen

_KV_PATH = os.path.join(os.path.dirname(__file__), "map_screen.kv")
Builder.load_file(_KV_PATH)


class MapScreen(BaseScreen):
    layout_slots = [MapLayout.HEADER, MapLayout.MAIN]

    def after_build(self) -> None:
        self.do("map.bind_interactions")
        self.do("map.reload")