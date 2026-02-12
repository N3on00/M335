from __future__ import annotations

from data.dtos.spot import SpotDTO
from data.repositories.base_http_repository import BaseHttpRepository, HttpRepoConfig
from data.services.api_client import ApiClient


class SpotsRepository(BaseHttpRepository[SpotDTO]):
    def __init__(self, api: ApiClient):
        super().__init__(
            api,
            HttpRepoConfig(
                resource_path="/spots",
                from_json=SpotDTO.from_json,
                to_json=lambda dto: dto.to_json(),
            ),
        )