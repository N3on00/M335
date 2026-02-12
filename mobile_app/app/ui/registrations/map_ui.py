from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

from core.registry import ui_action, ui_component
from data.dtos.spot import SpotDTO
from ui.layouts.map_layout import MapLayout
from ui.widgets.spot_create_popup import SpotDraft, SpotEditorPopup
from ui.widgets.spot_details_popup import SpotDetailsPopup
from ui.widgets.spot_map_widget import MapConfig, SpotMapWidget


_PICK_KEY = "spot_location_pick_draft"


def _get_map_widget(ctx) -> SpotMapWidget:
    ws = ctx.screen.get_slot_widgets(MapLayout.MAIN)
    for w in ws:
        if isinstance(w, SpotMapWidget):
            return w
    raise RuntimeError("SpotMapWidget not found in MapLayout.MAIN")


@ui_action(action_id="map.bind_interactions")
def map_bind_interactions(ctx):
    mw = _get_map_widget(ctx)

    def open_editor(draft: SpotDraft, *, submit_label: str):
        def submit(updated: SpotDraft):
            if updated.spot_id:
                ctx.app.controller("spots").update_spot(
                    spot_id=updated.spot_id,
                    title=updated.title,
                    description=updated.description,
                    tags=updated.tags,
                    lat=updated.lat,
                    lon=updated.lon,
                    images=updated.images_base64,
                )
            else:
                ctx.app.controller("spots").create_spot(
                    title=updated.title,
                    description=updated.description,
                    tags=updated.tags,
                    lat=updated.lat,
                    lon=updated.lon,
                    images=updated.images_base64,
                )
            ctx.screen.do("map.reload")

        def pick_location(pick_draft: SpotDraft):
            ctx.app.state.cache[_PICK_KEY] = pick_draft

        SpotEditorPopup(
            draft=draft,
            on_submit=submit,
            on_pick_location=pick_location,
            submit_label=submit_label,
        ).open()

    def on_map_tap(lat: float, lon: float):
        pick = ctx.app.state.cache.pop(_PICK_KEY, None)
        if isinstance(pick, SpotDraft):
            updated = SpotDraft(
                spot_id=pick.spot_id,
                title=pick.title,
                description=pick.description,
                tags=list(pick.tags),
                lat=float(lat),
                lon=float(lon),
                images_base64=list(pick.images_base64),
            )
            open_editor(updated, submit_label="Speichern" if updated.spot_id else "Erstellen")
            return

        draft = SpotDraft(
            spot_id=None,
            title="",
            description="",
            tags=[],
            lat=float(lat),
            lon=float(lon),
            images_base64=[],
        )
        open_editor(draft, submit_label="Erstellen")

    def on_marker_select(spot: SpotDTO):
        if not spot.id:
            return

        def on_edit():
            draft = SpotDraft(
                spot_id=spot.id,
                title=spot.title,
                description=spot.description,
                tags=list(spot.tags),
                lat=float(spot.lat),
                lon=float(spot.lon),
                images_base64=list(spot.images),
            )
            open_editor(draft, submit_label="Speichern")

        def on_delete():
            ctx.app.controller("spots").delete_spot(spot_id=spot.id)
            ctx.screen.do("map.reload")

        SpotDetailsPopup(spot=spot, on_edit=on_edit, on_delete=on_delete).open()

    mw.set_on_map_tap(on_map_tap)
    mw.set_on_marker_select(on_marker_select)


@ui_action(action_id="map.reload")
def map_reload(ctx):
    # Ensure interactions are bound even if after_build timing changes
    ctx.screen.do("map.bind_interactions")

    spots = ctx.app.controller("spots").list_spots()
    mw = _get_map_widget(ctx)
    mw.set_spots(spots)


@ui_component(slot=MapLayout.HEADER, component_id="map.topbar", order=10)
def map_topbar(ctx):
    bar = ctx.app.kv_factory("TopBar")()
    bar.orientation = "horizontal"

    btn_back = Button(
        text="←",
        size_hint_x=None,
        width="44dp",
        background_normal="",
        background_down="",
        color=(.2, .25, .23, 1),
    )
    btn_back.bind(on_release=lambda *_: ctx.screen.go("home"))

    title = Label(text="Explore Map", font_size="16sp", bold=True, color=(.08, .10, .10, 1))

    btn_reload = Button(
        text="Reload",
        size_hint_x=None,
        width="110dp",
        background_normal="",
        background_down="",
        color=(.2, .25, .23, 1),
    )
    btn_reload.bind(on_release=lambda *_: ctx.screen.do("map.reload"))

    bar.add_widget(btn_back)
    bar.add_widget(title)
    bar.add_widget(btn_reload)
    return bar


@ui_component(slot=MapLayout.MAIN, component_id="map.view", order=10)
def map_view(ctx):
    cfg = ctx.app.state.map_config
    return SpotMapWidget(cfg=MapConfig(**cfg))