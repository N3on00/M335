from __future__ import annotations

from dataclasses import replace
from typing import List

from data.dtos.spot import SpotDTO
from data.repositories.spots_repository import SpotsRepository


class SpotsService:
    def __init__(self, repo: SpotsRepository):
        self._repo = repo

    def list(self) -> List[SpotDTO]:
        return self._repo.list()

    def create(self, *, title: str, description: str, tags: List[str], lat: float, lon: float, images: List[str]) -> SpotDTO:
        dto = SpotDTO(id=None, title=title, description=description, tags=tags, lat=lat, lon=lon, images=images)
        created_id = self._repo.create(dto)
        return replace(dto, id=created_id) if created_id else dto

    def update(self, *, spot_id: str, title: str, description: str, tags: List[str], lat: float, lon: float, images: List[str]) -> bool:
        dto = SpotDTO(id=spot_id, title=title, description=description, tags=tags, lat=lat, lon=lon, images=images)
        return self._repo.update(spot_id, dto)

    def delete(self, *, spot_id: str) -> bool:
        return self._repo.delete(spot_id)

    def last_error(self) -> str | None:
        return self._repo.last_error()
