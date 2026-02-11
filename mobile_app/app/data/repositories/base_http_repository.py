from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from data.services.api_client import ApiClient

T = TypeVar("T")


@dataclass(frozen=True)
class HttpRepoConfig(Generic[T]):
    resource_path: str
    from_json: Callable[[Dict[str, Any]], T]
    to_json: Callable[[T], Dict[str, Any]]


class BaseHttpRepository(Generic[T]):
    """Generic CRUD repository over the FastAPI backend."""

    def __init__(self, api: ApiClient, cfg: HttpRepoConfig[T]):
        self._api = api
        self._cfg = cfg

    def list(self) -> List[T]:
        data = self._api.get_json(self._cfg.resource_path)
        if not isinstance(data, list):
            raise RuntimeError(f"Expected list for GET {self._cfg.resource_path}, got {type(data)}")
        return [self._cfg.from_json(x) for x in data]

    def get(self, item_id: str) -> Optional[T]:
        data = self._api.get_json(f"{self._cfg.resource_path}/{item_id}", allow_404=True)
        if data is None:
            return None
        if not isinstance(data, dict):
            raise RuntimeError(f"Expected dict for GET item, got {type(data)}")
        return self._cfg.from_json(data)

    def create(self, item: T) -> str:
        payload = self._cfg.to_json(item)
        data = self._api.post_json(self._cfg.resource_path, payload)
        if not isinstance(data, dict) or "id" not in data:
            raise RuntimeError(f"Expected {{'id': ...}} for POST {self._cfg.resource_path}, got {data}")
        return str(data["id"])

    def update(self, item_id: str, item: T) -> None:
        payload = self._cfg.to_json(item)
        self._api.put_json(f"{self._cfg.resource_path}/{item_id}", payload)

    def delete(self, item_id: str) -> None:
        self._api.delete_json(f"{self._cfg.resource_path}/{item_id}", allow_404=False)
