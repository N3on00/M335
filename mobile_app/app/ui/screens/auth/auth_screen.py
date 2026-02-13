from __future__ import annotations

import os

from kivy.lang import Builder

from ui.layouts.auth_layout import AuthLayout
from ui.screens.base_screen import BaseScreen


_KV_PATH = os.path.join(os.path.dirname(__file__), "auth_screen.kv")
Builder.load_file(_KV_PATH)


class AuthScreen(BaseScreen):
    layout_slots = [AuthLayout.HEADER, AuthLayout.MAIN, AuthLayout.FOOTER]
