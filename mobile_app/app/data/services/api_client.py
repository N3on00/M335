from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin
import urllib.request
import urllib.error


@dataclass(frozen=True)
class ApiClient:
    base_url: str
    timeout_s: float = 5.0

    def _url(self, path: str) -> str:
        # Ensure path begins with "/"
        if not path.startswith("/"):
            path = "/" + path
        return urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))

    @staticmethod
    def _read_body(resp) -> str:
        try:
            raw = resp.read()
            return raw.decode("utf-8", errors="replace") if raw else ""
        except Exception:
            return ""

    def _request(self, method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
        url = self._url(path)

        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            # urllib follows redirects for GET/HEAD automatically.
            # For POST, behavior can vary; FastAPI uses 307 to preserve method.
            # We handle it by catching 307 and re-issuing to the Location.
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = self._read_body(resp)
                if not body:
                    return {}
                return json.loads(body)
        except urllib.error.HTTPError as e:
            body = self._read_body(e)

            # Handle FastAPI trailing-slash redirect (307) manually
            if e.code == 307:
                loc = e.headers.get("Location")
                if loc:
                    # Re-issue same request to Location
                    req2 = urllib.request.Request(loc, data=data, headers=headers, method=method)
                    with urllib.request.urlopen(req2, timeout=self.timeout_s) as resp2:
                        body2 = self._read_body(resp2)
                        if not body2:
                            return {}
                        return json.loads(body2)

            raise RuntimeError(f"HTTP {e.code} on {url}: {body}") from e

    def get_json(self, path: str, *, allow_404: bool = False) -> Optional[Any]:
        try:
            return self._request("GET", path)
        except RuntimeError as e:
            if allow_404 and "HTTP 404" in str(e):
                return None
            raise

    def post_json(self, path: str, payload: Dict[str, Any]) -> Any:
        return self._request("POST", path, payload)

    def put_json(self, path: str, payload: Dict[str, Any]) -> Any:
        return self._request("PUT", path, payload)

    def delete_json(self, path: str, *, allow_404: bool = False) -> Optional[Any]:
        try:
            return self._request("DELETE", path)
        except RuntimeError as e:
            if allow_404 and "HTTP 404" in str(e):
                return None
            raise