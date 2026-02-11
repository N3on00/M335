from __future__ import annotations

from kivy.uix.button import Button
from kivy.uix.label import Label

from core.registry import ui_action, ui_component
from ui.layouts.home_layout import HomeLayout


# -------- Actions --------

@ui_action(action_id="nav.to_map")
def nav_to_map(ctx):
    ctx.screen.go("map")


@ui_action(action_id="home.refresh")
def home_refresh(ctx):
    """Demo: call controller -> service -> backend and show a short result."""
    try:
        spots = ctx.app.controller("spots").list_spots()
        msg = f"Spots im Backend: {len(spots)}"
    except Exception as e:
        msg = f"Backend nicht erreichbar: {e}"

    ctx.app.state.cache["home_status"] = msg

    for w in ctx.screen.get_slot_widgets(HomeLayout.MAIN):
        if getattr(w, "_home_status_label", False):
            w.text = msg


# -------- Components (per-slot) --------

@ui_component(slot=HomeLayout.HEADER, component_id="home.title", order=10)
def header_title(ctx):
    return Label(text="SpotOnSight", font_size="28sp", size_hint_y=None, height="42dp")


@ui_component(slot=HomeLayout.HEADER, component_id="home.subtitle", order=20)
def header_subtitle(ctx):
    return Label(
        text="Finde Orte zum Entspannen oder für Aktivitäten.",
        size_hint_y=None,
        height="28dp",
    )


@ui_component(slot=HomeLayout.MAIN, component_id="home.status", order=5)
def main_status(ctx):
    txt = ctx.app.state.cache.get("home_status", "Status: (noch nicht geladen)")
    lbl = Label(text=txt, size_hint_y=None, height="28dp")
    lbl._home_status_label = True
    return lbl


@ui_component(slot=HomeLayout.MAIN, component_id="home.cta.refresh", order=10)
def main_cta_refresh(ctx):
    btn = Button(text="Spots laden", size_hint_y=None, height="48dp")
    btn.bind(on_release=lambda *_: ctx.screen.do("home.refresh"))
    return btn


@ui_component(slot=HomeLayout.MAIN, component_id="home.cta.map", order=20)
def main_cta_map(ctx):
    btn = Button(text="Zur Karte", size_hint_y=None, height="48dp")
    btn.bind(on_release=lambda *_: ctx.screen.do("nav.to_map"))
    return btn


@ui_component(slot=HomeLayout.FOOTER, component_id="home.footer.hint", order=10)
def footer_hint(ctx):
    return Label(
        text="Hinweis: Map Screen ist aktuell ein Platzhalter (MapView folgt).",
        font_size="12sp",
        size_hint_y=None,
        height="22dp",
    )
