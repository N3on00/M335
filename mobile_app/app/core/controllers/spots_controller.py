from __future__ import annotations

from typing import List

from core.di import controller_provider
from data.dtos.spot import SpotDTO
from data.interfaces.spots_port import SpotsPort


class SpotsController(SpotsPort):
    def __init__(self, ctx):
        self._service = ctx.service("spots_service")

    def list_spots(self) -> List[SpotDTO]:
        return self._service.list()

    def create_spot(self, *, title: str, description: str, tags: List[str], lat: float, lon: float, images: List[str]) -> SpotDTO:
        return self._service.create(title=title, description=description, tags=tags, lat=lat, lon=lon, images=images)

    def update_spot(self, *, spot_id: str, title: str, description: str, tags: List[str], lat: float, lon: float, images: List[str]) -> SpotDTO:
        return self._service.update(spot_id=spot_id, title=title, description=description, tags=tags, lat=lat, lon=lon, images=images)

    def delete_spot(self, *, spot_id: str) -> bool:
        return self._service.delete(spot_id=spot_id)


@controller_provider(interface_id="spots")
def spots_controller(ctx) -> SpotsPort:
    return SpotsController(ctx)