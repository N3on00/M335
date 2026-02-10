from __future__ import annotations

from kivy.lang import Builder
from ui.screens.base_screen import BaseScreen

Builder.load_file("ui/screens/map/map_screen.kv")

class MapScreen(BaseScreen):
    name = "map"

    container_ids = [
        "map:header",
        "map:main",
    ]

    def after_build(self) -> None:
        # Placeholder hook; later we will initialize MapView here.
        pass
