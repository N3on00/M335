"""Import modules that register things via decorators.

Decorators execute at import time, so this is the single place that triggers registration.
"""


def bootstrap_registries() -> None:
    # Screens (load kv + classes)
    from ui.screens.home import home_screen  # noqa: F401
    from ui.screens.map import map_screen    # noqa: F401

    # UI components/actions
    from ui.registrations import home_ui     # noqa: F401
    from ui.registrations import map_ui      # noqa: F401

    # Service providers (data access)
    from data.registrations import services  # noqa: F401

    # Controller providers (UI bindings)
    from core.controllers import spots_controller  # noqa: F401
