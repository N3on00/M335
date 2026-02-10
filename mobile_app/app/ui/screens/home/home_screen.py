from __future__ import annotations

from kivy.lang import Builder
from ui.screens.base_screen import BaseScreen

Builder.load_file("ui/screens/home/home_screen.kv")

class HomeScreen(BaseScreen):
    name = "home"

    # Define containers this screen exposes for registry injection
    container_ids = [
        "home:header",
        "home:main",
        "home:footer",
    ]
