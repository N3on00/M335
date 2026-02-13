from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin
import urllib.parse
import urllib.request
import urllib.error


class ApiClientError(RuntimeError):
    def __init__(self, message: str, *, status_code: Optional[int] = None, url: str = "", body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.url = url
        self.body = body


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

    @staticmethod
    def _parse_json_body(body: str) -> Any:
        if not body:
            return {}
        try:
            return json.loads(body)
        except Exception:
            return {"raw": body}

    def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        content_type: str = "application/json",
        auth_token: Optional[str] = None,
    ) -> Any:
        url = self._url(path)

        data = None
        headers = {"Content-Type": content_type}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        if payload is not None:
            if content_type == "application/x-www-form-urlencoded":
                data = urllib.parse.urlencode(payload).encode("utf-8")
            else:
                data = json.dumps(payload).encode("utf-8")

        timeout_s = float(self.timeout_s)
        if method in ("POST", "PUT") and data is not None and len(data) > 250_000:
            timeout_s = max(timeout_s, 20.0)

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                body = self._read_body(resp)
                return self._parse_json_body(body)
        except urllib.error.HTTPError as e:
            body = self._read_body(e)

            if e.code == 307:
                loc = e.headers.get("Location")
                if loc:
                    if loc.startswith("/"):
                        loc = self._url(loc)
                    req2 = urllib.request.Request(loc, data=data, headers=headers, method=method)
                    with urllib.request.urlopen(req2, timeout=timeout_s) as resp2:
                        body2 = self._read_body(resp2)
                        return self._parse_json_body(body2)

            if e.code == 404:
                alt_path = path[:-1] if path.endswith("/") else (path + "/")
                alt_url = self._url(alt_path)
                req_alt = urllib.request.Request(alt_url, data=data, headers=headers, method=method)
                try:
                    with urllib.request.urlopen(req_alt, timeout=timeout_s) as resp_alt:
                        body_alt = self._read_body(resp_alt)
                        return self._parse_json_body(body_alt)
                except Exception:
                    pass

            raise ApiClientError(f"HTTP {e.code} on {url}", status_code=e.code, url=url, body=body) from e
        except urllib.error.URLError as e:
            raise ApiClientError(f"Network error on {url}: {e}", url=url) from e
        except TimeoutError as e:
            raise ApiClientError(f"Timeout on {url}", url=url) from e
        except Exception as e:
            raise ApiClientError(f"Unexpected API error on {url}: {e}", url=url) from e

    def get_json(self, path: str, *, allow_404: bool = False, auth_token: Optional[str] = None) -> Optional[Any]:
        try:
            return self._request("GET", path, auth_token=auth_token)
        except ApiClientError as e:
            if allow_404 and e.status_code == 404:
                return None
            raise

    def post_json(self, path: str, payload: Dict[str, Any], *, auth_token: Optional[str] = None) -> Any:
        return self._request("POST", path, payload, auth_token=auth_token)

    def post_form(self, path: str, payload: Dict[str, Any], *, auth_token: Optional[str] = None) -> Any:
        return self._request(
            "POST",
            path,
            payload,
            content_type="application/x-www-form-urlencoded",
            auth_token=auth_token,
        )

    def put_json(self, path: str, payload: Dict[str, Any], *, auth_token: Optional[str] = None) -> Any:
        return self._request("PUT", path, payload, auth_token=auth_token)

    def delete_json(self, path: str, *, allow_404: bool = False, auth_token: Optional[str] = None) -> Optional[Any]:
        try:
            return self._request("DELETE", path, auth_token=auth_token)
        except ApiClientError as e:
            if allow_404 and e.status_code == 404:
                return None
            raise
