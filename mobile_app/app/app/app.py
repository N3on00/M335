from __future__ import annotations

from kivy.app import App
from kivy.lang import Builder

from app.bootstrap import bootstrap_registries
from core.navigation import Navigation
from core.controller import UIController
from core.context import AppContext
from data.services.api_client import ApiClient
from data.services.spots_service import SpotsService
from data.state import AppState

KV_ROOT = "ui/kv/app.kv"

class SpotOnSightApp(App):
    def build(self):
        Builder.load_file(KV_ROOT)

        # 1) Data layer (services/state)
        state = AppState()
        api = ApiClient(base_url=state.config.api_base_url, timeout_s=state.config.request_timeout_s)
        services = {
            "spots": SpotsService(api),
        }

        # 2) Navigation + Controller + Context
        nav = Navigation()
        ctx = AppContext(state=state, services=services, nav=nav)

        controller = UIController(ctx)

        # 3) Bootstrap registries (decorators run on import)
        bootstrap_registries()

        # 4) Build screens (generic wiring)
        sm = nav.build_screen_manager(controller)
        return sm
