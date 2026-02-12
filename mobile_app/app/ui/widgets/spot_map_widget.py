from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout

from data.dtos.spot import SpotDTO

# MapView imports differ across versions. Some versions provide MapMarkerPopup,
# others only MapMarker. We try both and fail with a clear message if missing.
try:
    from kivy_garden.mapview import MapView, MapMarkerPopup  # type: ignore
    _MarkerBase = MapMarkerPopup
except Exception:
    try:
        from kivy_garden.mapview import MapView, MapMarker  # type: ignore
        _MarkerBase = MapMarker
    except Exception as e:
        raise ImportError(
            "kivy_garden.mapview is not available. Install it in your venv:\n"
            "  pip install kivy-garden\n"
            "  pip install kivy-garden.mapview\n"
            "If that fails, try:\n"
            "  python -m pip install kivy_garden.mapview\n"
        ) from e


@dataclass(frozen=True)
class MapConfig:
    default_lat: float = 47.3769
    default_lon: float = 8.5417
    default_zoom: int = 12
    tile_url: str | None = None
    tile_cache_key: str | None = None

    # Tap detection tuning
    tap_max_move_dp: float = 12.0       # movement threshold to still count as tap
    tap_max_time_s: float = 0.35        # optional time threshold


class SpotMarker(_MarkerBase):
    """Marker for a spot (works with MapMarkerPopup and MapMarker)."""

    def __init__(
        self,
        *,
        spot: SpotDTO,
        on_select: Optional[Callable[[SpotDTO], None]] = None,
    ):
        super().__init__(lat=float(spot.lat), lon=float(spot.lon))
        self._spot = spot
        self._on_select = on_select
        self.bind(on_touch_down=self._on_touch_down)

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            # Mark touch as "marker interaction" so the map does not treat it as a tap-to-create.
            touch.ud["spot_marker"] = True
            if self._on_select:
                self._on_select(self._spot)
            return True
        return False


class SpotMapWidget(BoxLayout):
    """Map widget wrapper for MapScreen.

    - set_spots(): clears and adds markers
    - tap on map triggers on_map_tap(lat, lon)
    - swipe/pan does NOT trigger on_map_tap
    """

    def __init__(self, *, cfg: MapConfig, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._cfg = cfg

        self._on_map_tap: Optional[Callable[[float, float], None]] = None
        self._on_marker_select: Optional[Callable[[SpotDTO], None]] = None

        self.map = MapView(
            zoom=cfg.default_zoom,
            lat=cfg.default_lat,
            lon=cfg.default_lon,
        )
        self._apply_config_best_effort(cfg)

        # Tap detection
        self._tap_max_move_px = float(dp(cfg.tap_max_move_dp))
        self.map.bind(on_touch_down=self._on_map_touch_down)
        self.map.bind(on_touch_up=self._on_map_touch_up)

        self.add_widget(self.map)

    # ---- Public API ----

    def set_on_map_tap(self, cb: Optional[Callable[[float, float], None]]) -> None:
        self._on_map_tap = cb

    def set_on_marker_select(self, cb: Optional[Callable[[SpotDTO], None]]) -> None:
        self._on_marker_select = cb

    def center(self) -> tuple[float, float]:
        return float(self.map.lat), float(self.map.lon)

    def get_center(self) -> tuple[float, float]:
        return self.center()

    def clear_markers(self) -> None:
        for child in list(self.map.children):
            if isinstance(child, _MarkerBase):
                self.map.remove_widget(child)

    def set_spots(self, spots: Iterable[SpotDTO]) -> None:
        self.clear_markers()
        for s in spots:
            if s.lat is None or s.lon is None:
                continue
            marker = SpotMarker(spot=s, on_select=self._on_marker_select)
            self.map.add_widget(marker)

    # ---- Internals ----

    def _apply_config_best_effort(self, cfg: MapConfig) -> None:
        src = getattr(self.map, "map_source", None) or getattr(self.map, "source", None)

        if cfg.tile_url and src is not None and hasattr(src, "url"):
            try:
                src.url = cfg.tile_url
            except Exception:
                pass

        if cfg.tile_cache_key and src is not None:
            for attr in ("cache_key", "cache_key_id"):
                if hasattr(src, attr):
                    try:
                        setattr(src, attr, cfg.tile_cache_key)
                        break
                    except Exception:
                        pass

    def _on_map_touch_down(self, instance, touch):
        if not self.map.collide_point(*touch.pos):
            return False

        # Track a possible tap
        touch.ud["tap_start_pos"] = (touch.x, touch.y)
        touch.ud["tap_start_t"] = time.monotonic()
        return False

    def _on_map_touch_up(self, instance, touch):
        if not self.map.collide_point(*touch.pos):
            return False

        # Do not treat marker clicks as map taps
        if touch.ud.get("spot_marker"):
            return False

        if not self._on_map_tap:
            return False

        start = touch.ud.get("tap_start_pos")
        start_t = touch.ud.get("tap_start_t")
        if not start or start_t is None:
            return False

        dx = float(touch.x - start[0])
        dy = float(touch.y - start[1])
        dist2 = dx * dx + dy * dy
        if dist2 > (self._tap_max_move_px * self._tap_max_move_px):
            return False

        if (time.monotonic() - float(start_t)) > float(self._cfg.tap_max_time_s):
            return False

        latlon = self._best_effort_latlon_from_touch(touch)
        if latlon is None:
            return False

        lat, lon = latlon
        self._on_map_tap(float(lat), float(lon))
        return False

    def _best_effort_latlon_from_touch(self, touch) -> Optional[tuple[float, float]]:
        fn = getattr(self.map, "get_latlon_at", None)
        if callable(fn):
            try:
                lat, lon = fn(touch.x, touch.y)
                return float(lat), float(lon)
            except Exception:
                pass

        # Fallback: current center
        try:
            return self.center()
        except Exception:
            return None