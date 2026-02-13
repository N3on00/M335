from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from kivy.clock import Clock
from kivy_garden.mapview import MapView, MapMarkerPopup
from kivy_garden.mapview.downloader import Downloader

from data.dtos.spot import SpotDTO


def _pick(cfg: Dict[str, Any], *keys: str, default=None):
    for k in keys:
        if k in cfg and cfg[k] is not None:
            return cfg[k]
    return default


@dataclass(frozen=True)
class MapConfig:
    lat: float = 47.3769
    lon: float = 8.5417
    zoom: int = 13

    @staticmethod
    def from_any(cfg: Any) -> "MapConfig":
        if isinstance(cfg, MapConfig):
            return cfg
        if not isinstance(cfg, dict):
            return MapConfig()

        lat_raw = _pick(cfg, "lat", "default_lat", default=47.3769)
        lon_raw = _pick(cfg, "lon", "default_lon", default=8.5417)
        zoom_raw = _pick(cfg, "zoom", "default_zoom", default=13)

        try:
            lat = 47.3769 if lat_raw is None else float(lat_raw)
        except (TypeError, ValueError):
            lat = 47.3769

        try:
            lon = 8.5417 if lon_raw is None else float(lon_raw)
        except (TypeError, ValueError):
            lon = 8.5417

        try:
            zoom = 13 if zoom_raw is None else int(zoom_raw)
        except (TypeError, ValueError):
            zoom = 13

        return MapConfig(lat=lat, lon=lon, zoom=zoom)


class SpotMarker(MapMarkerPopup):
    def __init__(self, spot: SpotDTO, on_select: Callable[[SpotDTO], None], **kwargs):
        super().__init__(**kwargs)
        self._spot = spot
        self._on_select = on_select

    def on_release(self):
        self._on_select(self._spot)


class SpotMapWidget(MapView):
    _TAP_MAX_SECONDS = 0.30
    _TAP_MAX_PX = 10.0
    _PAN_CENTER_EPS = 1e-7

    def __init__(self, *, cfg: Any, **kwargs):
        super().__init__(**kwargs)

        mc = MapConfig.from_any(cfg)
        self.lat = mc.lat
        self.lon = mc.lon
        self.zoom = mc.zoom

        self._spots: List[SpotDTO] = []
        self._markers: List[SpotMarker] = []
        self._on_map_tap: Optional[Callable[[float, float], None]] = None
        self._on_marker_select: Optional[Callable[[SpotDTO], None]] = None

        # Defensive cleanup for corrupt cached tiles
        Clock.schedule_interval(self._cleanup_bad_tiles, 2.0)

    # ----- Public API -----

    def set_spots(self, spots: List[SpotDTO]) -> None:
        self._spots = spots
        self._render_markers()

    def set_on_map_tap(self, cb: Callable[[float, float], None]) -> None:
        self._on_map_tap = cb

    def set_on_marker_select(self, cb: Callable[[SpotDTO], None]) -> None:
        self._on_marker_select = cb

    # ----- Interaction -----

    @staticmethod
    def _is_scroll_touch(touch) -> bool:
        if getattr(touch, "is_mouse_scrolling", False):
            return True
        btn = getattr(touch, "button", "")
        return btn in ("scrollup", "scrolldown", "scrollleft", "scrollright")

    @staticmethod
    def _is_primary_mouse_button(touch) -> bool:
        btn = getattr(touch, "button", "left")
        return btn == "left"

    def on_touch_down(self, touch):
        res = super().on_touch_down(touch)

        if not self.collide_point(*touch.pos):
            return res

        if self._is_scroll_touch(touch) or not self._is_primary_mouse_button(touch):
            touch.ud["sos_tap_candidate"] = False
            return res

        touch.ud["sos_tap_candidate"] = True
        touch.ud["sos_tap_start_pos"] = tuple(touch.pos)
        touch.ud["sos_tap_start_time"] = time.perf_counter()
        touch.ud["sos_tap_start_center"] = (float(self.lat), float(self.lon), int(self.zoom))
        return res

    def on_touch_move(self, touch):
        res = super().on_touch_move(touch)

        if not touch.ud.get("sos_tap_candidate"):
            return res

        sx, sy = touch.ud.get("sos_tap_start_pos", touch.pos)
        dx = float(touch.pos[0]) - float(sx)
        dy = float(touch.pos[1]) - float(sy)
        if (dx * dx + dy * dy) ** 0.5 > self._TAP_MAX_PX:
            touch.ud["sos_tap_candidate"] = False

        return res

    def on_touch_up(self, touch):
        res = super().on_touch_up(touch)

        if self._is_scroll_touch(touch):
            return res

        # If MapView marked it as pan/zoom, ignore as tap
        mv = touch.ud.get("mapview")
        if isinstance(mv, dict) and mv.get("mode") in ("pan", "zoom"):
            return res

        if not touch.ud.get("sos_tap_candidate"):
            return res

        if not self._is_primary_mouse_button(touch):
            return res

        started = float(touch.ud.get("sos_tap_start_time", 0.0))
        if started <= 0.0 or (time.perf_counter() - started) > self._TAP_MAX_SECONDS:
            return res

        sx, sy = touch.ud.get("sos_tap_start_pos", touch.pos)
        dx = float(touch.pos[0]) - float(sx)
        dy = float(touch.pos[1]) - float(sy)
        if (dx * dx + dy * dy) ** 0.5 > self._TAP_MAX_PX:
            return res

        start_lat, start_lon, start_zoom = touch.ud.get(
            "sos_tap_start_center", (float(self.lat), float(self.lon), int(self.zoom))
        )
        if int(self.zoom) != int(start_zoom):
            return res
        if abs(float(self.lat) - float(start_lat)) > self._PAN_CENTER_EPS:
            return res
        if abs(float(self.lon) - float(start_lon)) > self._PAN_CENTER_EPS:
            return res

        if self.collide_point(*touch.pos) and self._on_map_tap:
            lat, lon = self.get_latlon_at(*touch.pos)
            self._on_map_tap(float(lat), float(lon))
            return True

        return res

    # ----- Internals -----

    def _render_markers(self) -> None:
        for m in self._markers:
            try:
                self.remove_marker(m)
            except Exception:
                pass
        self._markers.clear()

        on_select = self._on_marker_select or (lambda _s: None)

        for s in self._spots:
            mk = SpotMarker(s, on_select=on_select, lat=s.lat, lon=s.lon)
            self.add_marker(mk)
            self._markers.append(mk)

    def _cleanup_bad_tiles(self, _dt):
        cache_dir = getattr(Downloader, "cache_dir", None)
        if not cache_dir or not os.path.isdir(cache_dir):
            return

        try:
            for root, _dirs, files in os.walk(cache_dir):
                for fn in files:
                    p = os.path.join(root, fn)
                    try:
                        if os.path.getsize(p) < 200:
                            os.remove(p)
                    except Exception:
                        pass
        except Exception:
            return
