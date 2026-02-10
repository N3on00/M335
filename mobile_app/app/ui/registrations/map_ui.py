from __future__ import annotations

from kivy.uix.label import Label
from kivy.uix.button import Button

from core.registry import ui_component, ui_action

@ui_action(action_id="nav.back_home")
def back_home(ctx):
    ctx.screen.go("home")

@ui_component(container_id="map:header", component_id="map.title", order=10)
def map_title(ctx):
    return Label(text="Karte", font_size="22sp", size_hint_y=None, height="36dp")

@ui_component(container_id="map:header", component_id="map.back", order=20)
def map_back_button(ctx):
    btn = Button(text="Zurück", size_hint_y=None, height="44dp")
    btn.bind(on_release=lambda *_: ctx.screen.do("nav.back_home"))
    return btn

@ui_component(container_id="map:main", component_id="map.placeholder", order=10)
def map_placeholder(ctx):
    return Label(
        text="Map Platzhalter. Nächster Schritt: kivy-garden.mapview + Touch/Drag/Zoom + Spot Marker.",
    )
