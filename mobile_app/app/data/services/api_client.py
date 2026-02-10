from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

class ApiClient:
    def __init__(self, base_url: str, timeout_s: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def get_json(self, path: str) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code} on {url}") from e
        except Exception as e:
            raise RuntimeError(f"Request failed: {url} -> {e}") from e

    def post_json(self, path: str, payload: dict) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            body = getattr(e, "read", lambda: b"")().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {e.code} on {url}: {body}") from e
        except Exception as e:
            raise RuntimeError(f"Request failed: {url} -> {e}") from e
