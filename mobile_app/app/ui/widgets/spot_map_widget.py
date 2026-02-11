from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from kivy.uix.boxlayout import BoxLayout

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

    # Optional custom tiles (not all versions support it)
    tile_url: str | None = None

    # Optional cache key (some versions support it via map_source/cache_key)
    tile_cache_key: str | None = None


class SpotMarker(_MarkerBase):
    """Marker for a spot (works with MapMarkerPopup and MapMarker)."""

    def __init__(self, *, lat: float, lon: float, title: str, on_select: Optional[Callable[[], None]] = None):
        super().__init__(lat=lat, lon=lon)
        self._title = title
        self._on_select = on_select
        self.bind(on_touch_down=self._on_touch_down)

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            if self._on_select:
                self._on_select()
            return True
        return False


class SpotMapWidget(BoxLayout):
    """Map widget wrapper used by the Map screen."""

    def __init__(self, *, cfg: MapConfig, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self._cfg = cfg

        self.map = MapView(
            zoom=cfg.default_zoom,
            lat=cfg.default_lat,
            lon=cfg.default_lon,
        )

        self._apply_config_best_effort(cfg)
        self.add_widget(self.map)

    def _apply_config_best_effort(self, cfg: MapConfig) -> None:
        src = getattr(self.map, "map_source", None) or getattr(self.map, "source", None)

        # Tiles URL
        if cfg.tile_url and src is not None:
            for attr in ("url",):
                if hasattr(src, attr):
                    try:
                        setattr(src, attr, cfg.tile_url)
                        break
                    except Exception:
                        pass

        # Cache key
        if cfg.tile_cache_key and src is not None:
            for attr in ("cache_key", "cache_key_id", "cache"):
                if hasattr(src, attr):
                    try:
                        setattr(src, attr, cfg.tile_cache_key)
                        break
                    except Exception:
                        pass

    def center(self) -> tuple[float, float]:
        return float(self.map.lat), float(self.map.lon)

    def clear_markers(self) -> None:
        for child in list(self.map.children):
            if isinstance(child, _MarkerBase):
                self.map.remove_widget(child)

    def add_spot_marker(self, *, lat: float, lon: float, title: str, on_select: Optional[Callable[[], None]] = None) -> None:
        marker = SpotMarker(lat=lat, lon=lon, title=title, on_select=on_select)
        self.map.add_widget(marker)