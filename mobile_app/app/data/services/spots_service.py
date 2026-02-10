from __future__ import annotations
from typing import List, Optional

from data.services.api_client import ApiClient
from data.dtos.spot import SpotDTO

class SpotsService:
    def __init__(self, api: ApiClient):
        self.api = api

    def list(self) -> List[SpotDTO]:
        # Backend endpoint can be adjusted later. Keep it centralized here.
        data = self.api.get_json("/spots")
        # Support either {"items":[...]} or plain list
        items = data.get("items", data) if isinstance(data, dict) else data
        return [SpotDTO(**x) for x in (items or [])]

    def create(self, dto: SpotDTO) -> SpotDTO:
        payload = dto.model_dump(exclude_none=True)
        data = self.api.post_json("/spots", payload)
        return SpotDTO(**data) if isinstance(data, dict) else dto
