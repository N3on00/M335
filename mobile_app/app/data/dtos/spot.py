from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


def _extract_id(data: Dict[str, Any]) -> Optional[str]:
    if "id" in data and data["id"] is not None:
        return str(data["id"])

    raw = data.get("_id")
    if raw is None:
        return None
    if isinstance(raw, dict) and "$oid" in raw:
        return str(raw["$oid"])
    return str(raw)


def _as_str_list(v: Any) -> List[str]:
    if not isinstance(v, list):
        return []
    return [str(x).strip() for x in v if str(x).strip()]


@dataclass(frozen=True)
class SpotDTO:
    id: Optional[str]
    title: str
    description: str
    tags: List[str]
    lat: float
    lon: float
    images: List[str]

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "SpotDTO":
        return SpotDTO(
            id=_extract_id(data),
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            tags=_as_str_list(data.get("tags", [])),
            lat=float(data.get("lat", 0.0)),
            lon=float(data.get("lon", 0.0)),
            images=_as_str_list(data.get("images", [])),
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "tags": list(self.tags),
            "lat": float(self.lat),
            "lon": float(self.lon),
            "images": list(self.images),
        }