from __future__ import annotations

from typing import List

from core.di import controller_provider
from data.dtos.spot import SpotDTO
from data.interfaces.spots_port import SpotsPort


class SpotsController(SpotsPort):
    """Controller binding UI to SpotsService."""

    def __init__(self, ctx):
        self._service = ctx.service("spots_service")

    def list_spots(self) -> List[SpotDTO]:
        return self._service.list()

    def create_spot(self, dto: SpotDTO) -> SpotDTO:
        return self._service.create(dto)


@controller_provider(interface_id="spots")
def spots_controller(ctx) -> SpotsPort:
    return SpotsController(ctx)
