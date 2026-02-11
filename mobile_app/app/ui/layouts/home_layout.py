from __future__ import annotations

from core.layout import LayoutSlot


class HomeLayout:
    """Typed layout slots for HomeScreen."""

    HEADER = LayoutSlot(key="home.header", kv_id="home_header")
    MAIN = LayoutSlot(key="home.main", kv_id="home_main")
    FOOTER = LayoutSlot(key="home.footer", kv_id="home_footer")
