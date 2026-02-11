from __future__ import annotations

from core.layout import LayoutSlot


class MapLayout:
    """Typed layout slots for MapScreen."""

    HEADER = LayoutSlot(key="map.header", kv_id="map_header")
    MAIN = LayoutSlot(key="map.main", kv_id="map_main")
