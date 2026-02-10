from __future__ import annotations
from threading import Thread
from typing import Callable, Any
from kivy.clock import Clock

def run_bg(task: Callable[[], Any], on_ok: Callable[[Any], None], on_err: Callable[[Exception], None]) -> None:
    def worker():
        try:
            res = task()
            Clock.schedule_once(lambda *_: on_ok(res), 0)
        except Exception as e:
            Clock.schedule_once(lambda *_: on_err(e), 0)
    Thread(target=worker, daemon=True).start()
