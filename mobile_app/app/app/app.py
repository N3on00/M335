from __future__ import annotations

import os

from kivy.app import App
from kivy.lang import Builder
from kivy_garden.mapview.downloader import Downloader

from app.bootstrap import bootstrap_registries
from core.context import AppContext
from core.navigation import Navigation
from core.controller import UIController
from data.state import AppState


def _tiles_cache_dir() -> str:
    # Put tile cache into project-local folder so you can delete it easily
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(base, ".tile_cache")
    os.makedirs(path, exist_ok=True)
    return path


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _session_cache_file() -> str:
    path = os.path.join(_project_root(), "cache", "session.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


class SpotOnSightApp(App):
    def build(self):
        Builder.load_file("ui/kv/app.kv")

        state = AppState()
        state.load_from_file(os.path.join(_project_root(), "app_config.json"))
        state.load_session(_session_cache_file())
        self._state = state
        state.cache = getattr(state, "cache", {})  # ensure exists
        state.map_config = getattr(state, "map_config", {
            "lat": 47.3769,
            "lon": 8.5417,
            "zoom": 13,
        })

        # Configure map tile downloader cache
        Downloader.cache_dir = _tiles_cache_dir()

        nav = Navigation()
        ctx = AppContext(state=state, nav=nav)

        bootstrap_registries()

        if state.auth_token:
            try:
                auth_service = ctx.service("auth_service")
                if not auth_service.refresh_me():
                    auth_service.logout()
            except Exception:
                state.auth_token = None
                state.current_user = None

        controller = UIController(ctx)
        sm = nav.build_screen_manager(controller)
        return sm

    def on_stop(self):
        state = getattr(self, "_state", None)
        if state is None:
            return
        try:
            state.save_session(_session_cache_file())
        except Exception:
            return
