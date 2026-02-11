from __future__ import annotations

from typing import List, Protocol

from data.dtos.spot import SpotDTO


class SpotsPort(Protocol):
    def list_spots(self) -> List[SpotDTO]:
        raise NotImplementedError

    def create_spot(self, dto: SpotDTO) -> SpotDTO:
        raise NotImplementedError
