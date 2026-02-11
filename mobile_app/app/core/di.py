from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass(frozen=True)
class ServiceSpec:
    service_id: str
    factory: Callable[[Any], Any]  # (AppContext) -> service


@dataclass(frozen=True)
class ControllerSpec:
    interface_id: str
    factory: Callable[[Any], Any]  # (AppContext) -> controller


_SERVICES: Dict[str, ServiceSpec] = {}
_CONTROLLERS: Dict[str, ControllerSpec] = {}


def service_provider(*, service_id: str):
    """Register a service factory by id."""

    def decorator(factory: Callable[[Any], Any]) -> Callable[[Any], Any]:
        _SERVICES[service_id] = ServiceSpec(service_id=service_id, factory=factory)
        return factory

    return decorator


def controller_provider(*, interface_id: str):
    """Register a controller factory by interface id."""

    def decorator(factory: Callable[[Any], Any]) -> Callable[[Any], Any]:
        _CONTROLLERS[interface_id] = ControllerSpec(interface_id=interface_id, factory=factory)
        return factory

    return decorator


def get_service_spec(service_id: str) -> Optional[ServiceSpec]:
    return _SERVICES.get(service_id)


def get_controller_spec(interface_id: str) -> Optional[ControllerSpec]:
    return _CONTROLLERS.get(interface_id)
