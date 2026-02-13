from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from core.registry import ui_component
from ui.layouts.home_layout import HomeLayout


@ui_component(slot=HomeLayout.HEADER, component_id="home.hero", order=10)
def home_hero(ctx):
    root = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    auth = ctx.app.service("auth_service")
    if not auth.is_authenticated():
        ctx.screen.go("auth")
        return root

    top = BoxLayout(orientation="horizontal", size_hint_y=None, height="36dp")
    top.add_widget(Label(text="", size_hint_x=1))
    logout = Button(
        text="Logout",
        size_hint_x=None,
        width="100dp",
        background_normal="",
        background_down="",
        color=(.2, .25, .23, 1),
    )

    def _logout(*_):
        auth.logout()
        ctx.screen.go("auth")

    logout.bind(on_release=_logout)
    top.add_widget(logout)
    root.add_widget(top)

    # Logo circle
    logo_row = BoxLayout(orientation="horizontal", size_hint_y=None, height="60dp")
    logo_row.add_widget(Label(text="", size_hint_x=1))
    logo = ctx.app.kv_factory("IconCircle")()
    logo.add_widget(Label(text="🗺", font_size="20sp", halign="center", valign="middle"))
    logo_row.add_widget(logo)
    logo_row.add_widget(Label(text="", size_hint_x=1))
    root.add_widget(logo_row)

    # Title + subtitle (centered)
    title = Label(text="SpotOnSight", font_size="28sp", bold=True, color=(.08, .10, .10, 1), size_hint_y=None, height="34dp")
    subtitle = Label(text="Discover places worth your time", font_size="14sp", color=(.45, .48, .50, 1), size_hint_y=None, height="22dp")
    root.add_widget(title)
    root.add_widget(subtitle)
    return root


@ui_component(slot=HomeLayout.MAIN, component_id="home.actions", order=10)
def home_actions(ctx):
    # Two large cards like Figma
    root = BoxLayout(orientation="vertical", spacing=12, size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    def card(title: str, subtitle: str, icon: str, on_press):
        c = ctx.app.kv_factory("RoundedCard")()
        c.orientation = "horizontal"
        c.spacing = 12
        c.size_hint_y = None
        c.height = "86dp"

        ic = ctx.app.kv_factory("IconCircle")()
        ic.size = ("44dp", "44dp")
        ic.add_widget(Label(text=icon, font_size="18sp", halign="center", valign="middle"))
        c.add_widget(ic)

        texts = BoxLayout(orientation="vertical", spacing=2)
        texts.add_widget(Label(text=title, font_size="16sp", bold=True, color=(.08, .10, .10, 1), halign="left"))
        texts.add_widget(Label(text=subtitle, font_size="13sp", color=(.45, .48, .50, 1), halign="left"))
        c.add_widget(texts)

        # Make whole card clickable by binding to touch
        def _on_touch_up(w, touch):
            if c.collide_point(*touch.pos):
                on_press()
                return True
            return False

        c.bind(on_touch_up=_on_touch_up)
        return c

    root.add_widget(card(
        "Explore Map",
        "Browse nearby places on an interactive map",
        "🗺",
        lambda: ctx.screen.go("map"),
    ))

    root.add_widget(card(
        "Discover Spots",
        "Find curated places based on your interests",
        "🧭",
        lambda: None,  # later: ctx.screen.go("discover")
    ))

    return root


@ui_component(slot=HomeLayout.FOOTER, component_id="home.coming_soon", order=10)
def home_coming_soon(ctx):
    root = BoxLayout(orientation="vertical", spacing=10, size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    root.add_widget(Label(text="Coming Soon", font_size="13sp", color=(.45, .48, .50, 1), size_hint_y=None, height="18dp"))

    row = BoxLayout(orientation="horizontal", spacing=12, size_hint_y=None, height="96dp")

    def tile(title: str, icon: str):
        t = ctx.app.kv_factory("SoftTile")()
        t.orientation = "vertical"
        t.spacing = 6
        t.add_widget(Label(text=icon, font_size="18sp", color=(.45, .48, .50, 1)))
        t.add_widget(Label(text=title, font_size="13sp", color=(.45, .48, .50, 1)))
        return t

    row.add_widget(tile("Favorites", "♡"))
    row.add_widget(tile("Trending", "↗"))
    root.add_widget(row)

    return root
