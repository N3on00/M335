from __future__ import annotations

from typing import List, Protocol

from data.dtos.spot import SpotDTO


class SpotsPort(Protocol):
    def list_spots(self) -> List[SpotDTO]:
        raise NotImplementedError

    def create_spot(self, *, title: str, description: str, tags: List[str], lat: float, lon: float, images: List[str]) -> SpotDTO:
        raise NotImplementedError

    def update_spot(self, *, spot_id: str, title: str, description: str, tags: List[str], lat: float, lon: float, images: List[str]) -> SpotDTO:
        raise NotImplementedError

    def delete_spot(self, *, spot_id: str) -> bool:
        raise NotImplementedError