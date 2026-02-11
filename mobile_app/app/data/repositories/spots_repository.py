from __future__ import annotations

from typing import Any, Dict

from data.dtos.spot import SpotDTO
from data.repositories.base_http_repository import BaseHttpRepository, HttpRepoConfig
from data.services.api_client import ApiClient


def _normalize_mongo_json(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize json_util output from backend.

    Mongo ObjectId is returned as: {"_id": {"$oid": "..."}}
    We map it into DTO's `id` field and drop `_id`.
    """
    out = dict(doc)
    raw_id = out.pop("_id", None)
    if isinstance(raw_id, dict) and "$oid" in raw_id:
        out["id"] = raw_id["$oid"]
    elif raw_id is not None and "id" not in out:
        out["id"] = str(raw_id)
    return out


class SpotsRepository(BaseHttpRepository[SpotDTO]):
    def __init__(self, api: ApiClient):
        super().__init__(
            api,
            HttpRepoConfig(
                resource_path="/spots",
                from_json=lambda d: SpotDTO(**_normalize_mongo_json(d)),
                to_json=lambda dto: dto.model_dump(exclude_none=True),
            ),
        )
