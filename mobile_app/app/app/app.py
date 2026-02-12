from __future__ import annotations

from kivy.app import App
from kivy.lang import Builder
from ui import registrations
from app.bootstrap import bootstrap_registries
from core.context import AppContext
from core.controller import UIController
from core.navigation import Navigation
from data.state import AppState

KV_ROOT = "ui/kv/app.kv"


class SpotOnSightApp(App):
    def build(self):
        Builder.load_file(KV_ROOT)

        # State + navigation + context
        state = AppState()
        nav = Navigation()
        ctx = AppContext(state=state, nav=nav)

        # Register decorator-based providers (services, controllers, ui components/actions)
        bootstrap_registries()

        controller = UIController(ctx)
        sm = nav.build_screen_manager(controller)
        return sm
