"""Import modules that register UI components/actions via decorators.

Decorators execute at import time, so this is the single place that triggers registration.
You add new features by creating new modules and adding ONE import here (still no controller edits).
"""

def bootstrap_registries() -> None:
    # Screens
    from ui.screens.home import home_screen  # noqa: F401
    from ui.screens.map import map_screen    # noqa: F401

    # Registrations
    from ui.registrations import home_ui     # noqa: F401
    from ui.registrations import map_ui      # noqa: F401
