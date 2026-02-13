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

    def __init__(
        self,
        api: ApiClient,
        cfg: HttpRepoConfig[T],
        auth_token_provider: Optional[Callable[[], Optional[str]]] = None,
    ):
        self._api = api
        self._cfg = cfg
        self._last_error: Optional[str] = None
        self._auth_token_provider = auth_token_provider or (lambda: None)

    def _auth_token(self) -> Optional[str]:
        try:
            return self._auth_token_provider()
        except Exception:
            return None

    def last_error(self) -> Optional[str]:
        return self._last_error

    def _set_last_error(self, error: Optional[Exception]) -> None:
        self._last_error = None if error is None else str(error)

    def list(self) -> List[T]:
        try:
            data = self._api.get_json(self._cfg.resource_path, auth_token=self._auth_token())
            self._set_last_error(None)
        except Exception as e:
            self._set_last_error(e)
            return []

        if not isinstance(data, list):
            return []

        out: List[T] = []
        for x in data:
            if not isinstance(x, dict):
                continue
            try:
                out.append(self._cfg.from_json(x))
            except Exception as e:
                self._set_last_error(e)
                continue
        return out

    def get(self, item_id: str) -> Optional[T]:
        try:
            data = self._api.get_json(
                f"{self._cfg.resource_path}/{item_id}",
                allow_404=True,
                auth_token=self._auth_token(),
            )
            self._set_last_error(None)
        except Exception as e:
            self._set_last_error(e)
            return None

        if data is None:
            return None
        if not isinstance(data, dict):
            return None

        try:
            return self._cfg.from_json(data)
        except Exception as e:
            self._set_last_error(e)
            return None

    def create(self, item: T) -> Optional[str]:
        payload = self._cfg.to_json(item)
        try:
            data = self._api.post_json(self._cfg.resource_path, payload, auth_token=self._auth_token())
            self._set_last_error(None)
        except Exception as e:
            self._set_last_error(e)
            return None

        if not isinstance(data, dict) or "id" not in data:
            return None
        try:
            return str(data["id"])
        except Exception as e:
            self._set_last_error(e)
            return None

    def update(self, item_id: str, item: T) -> bool:
        payload = self._cfg.to_json(item)
        try:
            self._api.put_json(f"{self._cfg.resource_path}/{item_id}", payload, auth_token=self._auth_token())
            self._set_last_error(None)
            return True
        except Exception as e:
            self._set_last_error(e)
            return False

    def delete(self, item_id: str) -> bool:
        try:
            self._api.delete_json(
                f"{self._cfg.resource_path}/{item_id}",
                allow_404=True,
                auth_token=self._auth_token(),
            )
            self._set_last_error(None)
            return True
        except Exception as e:
            self._set_last_error(e)
            return False
