from __future__ import annotations

from core.layout import LayoutSlot


class AuthLayout:
    HEADER = LayoutSlot(key="auth.header", kv_id="auth_header")
    MAIN = LayoutSlot(key="auth.main", kv_id="auth_main")
    FOOTER = LayoutSlot(key="auth.footer", kv_id="auth_footer")
