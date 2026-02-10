from __future__ import annotations

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

from core.registry import ui_component, ui_action

# -------- Actions --------

@ui_action(action_id="nav.to_map")
def nav_to_map(ctx):
    ctx.screen.go("map")

@ui_action(action_id="home.refresh")
def home_refresh(ctx):
    # Keep this as an example action.
    # Later: load spots, show counts, etc.
    ctx.app.state.cache["home_last_refresh"] = "ok"

# -------- Components (per-container) --------

@ui_component(container_id="home:header", component_id="home.title", order=10)
def header_title(ctx):
    return Label(text="SpotOnSight", font_size="28sp", size_hint_y=None, height="42dp")

@ui_component(container_id="home:header", component_id="home.subtitle", order=20)
def header_subtitle(ctx):
    return Label(
        text="Finde Orte zum Entspannen oder für Aktivitäten.",
        size_hint_y=None,
        height="28dp"
    )

@ui_component(container_id="home:main", component_id="home.cta.map", order=10)
def main_cta_map(ctx):
    btn = Button(text="Zur Karte", size_hint_y=None, height="48dp")
    btn.bind(on_release=lambda *_: ctx.app.nav.go("map") if False else ctx.screen.do("nav.to_map"))
    return btn

@ui_component(container_id="home:main", component_id="home.cta.refresh", order=20)
def main_cta_refresh(ctx):
    btn = Button(text="Refresh (Demo Action)", size_hint_y=None, height="48dp")
    btn.bind(on_release=lambda *_: ctx.screen.do("home.refresh"))
    return btn

@ui_component(container_id="home:footer", component_id="home.footer.hint", order=10)
def footer_hint(ctx):
    return Label(
        text="Hinweis: Map Screen ist aktuell ein Platzhalter (MapView folgt).",
        font_size="12sp",
        size_hint_y=None,
        height="22dp"
    )
