from __future__ import annotations

from typing import List

from data.dtos.spot import SpotDTO
from data.repositories.spots_repository import SpotsRepository


class SpotsService:
    """Use-cases around spots."""

    def __init__(self, repo: SpotsRepository):
        self._repo = repo

    def list(self) -> List[SpotDTO]:
        return self._repo.list()

    def create(self, dto: SpotDTO) -> SpotDTO:
        new_id = self._repo.create(dto)
        created = self._repo.get(new_id)
        return created or SpotDTO(id=new_id, **dto.model_dump(exclude={"id"}, exclude_none=True))
