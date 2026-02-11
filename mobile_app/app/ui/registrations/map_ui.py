from __future__ import annotations

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from core.registry import ui_action, ui_component
from data.dtos.spot import SpotDTO
from ui.layouts.map_layout import MapLayout
from ui.widgets.spot_create_popup import SpotCreatePopup
from ui.widgets.spot_map_widget import MapConfig, SpotMapWidget


@ui_action(action_id="nav.to_home")
def nav_to_home(ctx):
    ctx.screen.go("home")


@ui_action(action_id="map.reload")
def map_reload(ctx):
    spots = ctx.app.controller("spots").list_spots()
    ctx.app.state.cache["map.spots"] = spots

    mw = getattr(ctx.screen, "map_widget", None)
    if mw is not None:
        mw.set_spots(spots)


@ui_action(action_id="map.create_at_center")
def map_create_at_center(ctx):
    mw = getattr(ctx.screen, "map_widget", None)
    if mw is None:
        return

    lat, lon = mw.get_center()

    def submit(payload: dict) -> None:
        dto = SpotDTO(**payload)
        ctx.app.controller("spots").create_spot(dto)
        ctx.screen.do("map.reload")

    SpotCreatePopup(lat=lat, lon=lon, on_submit=submit).open()


@ui_component(slot=MapLayout.HEADER, component_id="map.header", order=10)
def header(ctx):
    row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8), padding=[dp(10), dp(6), dp(10), dp(6)])

    title = Label(text="Karte", font_size="20sp")

    btn_reload = Button(text="Reload", size_hint_x=None, width=dp(90))
    btn_back = Button(text="Zurück", size_hint_x=None, width=dp(90))

    btn_reload.bind(on_release=lambda *_: ctx.screen.do("map.reload"))
    btn_back.bind(on_release=lambda *_: ctx.screen.do("nav.to_home"))

    row.add_widget(title)
    row.add_widget(btn_reload)
    row.add_widget(btn_back)
    return row


@ui_component(slot=MapLayout.MAIN, component_id="map.view", order=10)
def map_view(ctx):
    cfg = ctx.app.state.config
    map_cfg = MapConfig(
        default_lat=cfg.map_default_lat,
        default_lon=cfg.map_default_lon,
        default_zoom=int(cfg.map_default_zoom),
        tile_url=cfg.map_tile_url,
        tile_cache_key=cfg.map_tile_cache_key,
    )

    root = BoxLayout(orientation="vertical")
    mw = SpotMapWidget(cfg=map_cfg)
    root.add_widget(mw)

    bar = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8), padding=[dp(10), dp(6), dp(10), dp(6)])
    btn_add = Button(text="Spot hinzufügen (Center)")
    btn_add.bind(on_release=lambda *_: ctx.screen.do("map.create_at_center"))
    bar.add_widget(btn_add)

    root.add_widget(bar)

    # store reference for actions (after_build will also pick it up)
    ctx.screen.map_widget = mw
    return root
