from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from data.services.api_client import ApiClient
from data.state import AppState


@dataclass
class AuthService:
    _api: ApiClient
    _state: AppState
    _last_error: Optional[str] = None

    def last_error(self) -> Optional[str]:
        return self._last_error

    def _clear_error(self) -> None:
        self._last_error = None

    def _set_error(self, e: Exception | str) -> None:
        self._last_error = str(e)

    def _apply_session(self, payload: Dict[str, Any]) -> bool:
        token = payload.get("access_token")
        user = payload.get("user")
        if not isinstance(token, str) or not token.strip() or not isinstance(user, dict):
            self._set_error("Invalid auth response from backend")
            return False

        self._state.auth_token = token.strip()
        self._state.current_user = dict(user)
        self._clear_error()
        return True

    def is_authenticated(self) -> bool:
        return bool(self._state.auth_token)

    def register(self, *, username: str, email: str, password: str, display_name: str) -> bool:
        payload = {
            "username": username,
            "email": email,
            "password": password,
            "display_name": display_name,
        }
        try:
            data = self._api.post_json("/auth/register", payload)
        except Exception as e:
            self._set_error(e)
            return False
        return self._apply_session(data if isinstance(data, dict) else {})

    def login(self, *, username_or_email: str, password: str) -> bool:
        payload = {
            "username": username_or_email,
            "password": password,
        }
        try:
            data = self._api.post_form("/auth/login", payload)
        except Exception as e:
            self._set_error(e)
            return False
        return self._apply_session(data if isinstance(data, dict) else {})

    def logout(self) -> None:
        self._state.auth_token = None
        self._state.current_user = None

    def refresh_me(self) -> bool:
        if not self._state.auth_token:
            self._set_error("Not authenticated")
            return False
        try:
            user = self._api.get_json("/social/me", auth_token=self._state.auth_token)
        except Exception as e:
            self._set_error(e)
            return False
        if not isinstance(user, dict):
            self._set_error("Invalid user profile response")
            return False
        self._state.current_user = dict(user)
        self._clear_error()
        return True
