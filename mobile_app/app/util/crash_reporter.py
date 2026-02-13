from __future__ import annotations

import json
import os
import platform
import sys
import threading
import traceback
import urllib.error
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional
from urllib.parse import urljoin


_INSTALLED = False
_LOCK = threading.Lock()
_SENDING = False
_ORIG_SYS_EXCEPTHOOK = sys.excepthook
_ORIG_THREAD_EXCEPTHOOK = getattr(threading, "excepthook", None)
_ORIG_UNRAISABLE_HOOK = getattr(sys, "unraisablehook", None)


def _project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _cache_file_path() -> str:
    cache_dir = os.path.join(_project_root(), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "client_error_reports.jsonl")


def _api_base_url() -> str:
    env_url = (os.getenv("SOS_API_BASE_URL") or "").strip()
    if env_url:
        return env_url

    cfg_path = os.path.join(_project_root(), "app_config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = data.get("config", {}) if isinstance(data, dict) else {}
            base_url = str(cfg.get("api_base_url", "")).strip()
            if base_url:
                return base_url
        except Exception:
            pass

    return "http://127.0.0.1:8000"


def _url(path: str) -> str:
    base_url = _api_base_url().rstrip("/") + "/"
    return urljoin(base_url, path.lstrip("/"))


def _append_local(payload: Dict[str, Any]) -> None:
    try:
        with open(_cache_file_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _post_remote(payload: Dict[str, Any]) -> None:
    global _SENDING

    with _LOCK:
        if _SENDING:
            return
        _SENDING = True

    try:
        body = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        urls = [_url("/client-errors"), _url("/client-errors/")]
        for u in urls:
            req = urllib.request.Request(u, data=body, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=5.0):
                    return
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    continue
            except Exception:
                continue
    finally:
        with _LOCK:
            _SENDING = False


def _build_payload(
    *,
    exc_type: Optional[type],
    exc_value: Optional[BaseException],
    exc_tb,
    source: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    stacktrace = ""
    if exc_type is not None and exc_value is not None:
        stacktrace = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    elif exc_value is not None:
        stacktrace = "".join(traceback.format_exception(type(exc_value), exc_value, exc_value.__traceback__))

    payload = {
        "kind": "exception",
        "source": source,
        "message": str(exc_value) if exc_value is not None else "Unhandled exception",
        "exception_type": exc_type.__name__ if exc_type is not None else (type(exc_value).__name__ if exc_value else None),
        "stacktrace": stacktrace,
        "context": context or {},
        "platform": platform.platform(),
        "python_version": sys.version.split(" ")[0],
        "created_at": datetime.utcnow().isoformat(),
    }
    return payload


def report_exception(
    exc: BaseException,
    *,
    source: str = "handled",
    context: Optional[Dict[str, Any]] = None,
) -> None:
    payload = _build_payload(
        exc_type=type(exc),
        exc_value=exc,
        exc_tb=exc.__traceback__,
        source=source,
        context=context,
    )
    _append_local(payload)
    _post_remote(payload)


def _sys_excepthook(exc_type, exc_value, exc_tb):
    try:
        payload = _build_payload(exc_type=exc_type, exc_value=exc_value, exc_tb=exc_tb, source="sys.excepthook")
        _append_local(payload)
        _post_remote(payload)
    finally:
        _ORIG_SYS_EXCEPTHOOK(exc_type, exc_value, exc_tb)


def _thread_excepthook(args):
    try:
        payload = _build_payload(
            exc_type=args.exc_type,
            exc_value=args.exc_value,
            exc_tb=args.exc_traceback,
            source="threading.excepthook",
            context={"thread": getattr(args.thread, "name", "unknown")},
        )
        _append_local(payload)
        _post_remote(payload)
    finally:
        if _ORIG_THREAD_EXCEPTHOOK is not None:
            _ORIG_THREAD_EXCEPTHOOK(args)


def _unraisable_hook(unraisable):
    try:
        payload = _build_payload(
            exc_type=unraisable.exc_type,
            exc_value=unraisable.exc_value,
            exc_tb=unraisable.exc_traceback,
            source="sys.unraisablehook",
            context={"object": repr(unraisable.object)},
        )
        _append_local(payload)
        _post_remote(payload)
    finally:
        if _ORIG_UNRAISABLE_HOOK is not None:
            _ORIG_UNRAISABLE_HOOK(unraisable)


def install_crash_reporting() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    sys.excepthook = _sys_excepthook
    if hasattr(threading, "excepthook"):
        threading.excepthook = _thread_excepthook
    if hasattr(sys, "unraisablehook"):
        sys.unraisablehook = _unraisable_hook

    _INSTALLED = True
