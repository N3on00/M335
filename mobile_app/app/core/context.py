from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from kivy.factory import Factory

from core.di import get_controller_spec, get_service_spec
from core.navigation import Navigation
from data.state import AppState


@dataclass
class AppContext:
    """
    Holds app state + navigation and provides DI access via decorator-registered specs.

    Required by UI registrations:
      - ctx.app.service("...") / ctx.app.controller("...")

    Optional UI convenience:
      - ctx.app.kv_factory("RoundedCard")() etc.
    """
    state: AppState
    nav: Navigation

    _services: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _controllers: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def service(self, service_id: str) -> Any:
        if service_id in self._services:
            return self._services[service_id]

        spec = get_service_spec(service_id)
        if not spec:
            raise RuntimeError(f"Unknown service_id: {service_id}")

        inst = spec.factory(self)
        self._services[service_id] = inst
        return inst

    def controller(self, interface_id: str) -> Any:
        if interface_id in self._controllers:
            return self._controllers[interface_id]

        spec = get_controller_spec(interface_id)
        if not spec:
            raise RuntimeError(f"Unknown interface_id: {interface_id}")

        inst = spec.factory(self)
        self._controllers[interface_id] = inst
        return inst

    def kv_factory(self, name: str):
        return getattr(Factory, name)