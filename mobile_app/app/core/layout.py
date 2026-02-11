from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutSlot:
    """A typed reference to a place in a screen layout.

    - key: registry key used for component injection (stable, python-defined)
    - kv_id: Kivy `id:` to mount widgets into
    """

    key: str
    kv_id: str
