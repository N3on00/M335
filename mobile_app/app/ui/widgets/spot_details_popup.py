from __future__ import annotations

import base64
from io import BytesIO

from kivy.core.image import Image as CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup

from data.dtos.spot import SpotDTO
from ui.widgets.notify_popup import notify


class SpotDetailsPopup(Popup):
    def __init__(self, *, spot: SpotDTO, on_edit, on_delete, **kwargs):
        super().__init__(title="Spot Details", size_hint=(0.92, 0.92), auto_dismiss=True, **kwargs)
        self._spot = spot
        self._on_edit = on_edit
        self._on_delete = on_delete

        self._images = list(spot.images or [])
        self._idx = 0
        self._invalid_notified = set()

        root = BoxLayout(orientation="vertical", spacing=8, padding=12)

        root.add_widget(Label(text=spot.title, size_hint_y=None, height="28dp"))
        if spot.description:
            root.add_widget(Label(text=spot.description, size_hint_y=None, height="60dp"))
        if spot.tags:
            root.add_widget(Label(text=" • ".join(spot.tags), size_hint_y=None, height="28dp"))

        root.add_widget(Label(text=f"{spot.lat:.6f}, {spot.lon:.6f}", size_hint_y=None, height="24dp"))

        self._img = Image(allow_stretch=True, keep_ratio=True, size_hint_y=1)
        root.add_widget(self._img)

        nav = BoxLayout(orientation="horizontal", size_hint_y=None, height="44dp", spacing=8)
        btn_prev = Button(text="Prev")
        btn_next = Button(text="Next")
        self._info = Label(text="", size_hint_x=1)
        nav.add_widget(btn_prev)
        nav.add_widget(btn_next)
        nav.add_widget(self._info)
        root.add_widget(nav)

        actions = BoxLayout(orientation="horizontal", size_hint_y=None, height="48dp", spacing=8)
        btn_edit = Button(text="Edit")
        btn_del = Button(text="Delete")
        btn_close = Button(text="Close")
        actions.add_widget(btn_edit)
        actions.add_widget(btn_del)
        actions.add_widget(btn_close)
        root.add_widget(actions)

        self.content = root

        btn_prev.bind(on_release=lambda *_: self._step(-1))
        btn_next.bind(on_release=lambda *_: self._step(+1))
        btn_edit.bind(on_release=lambda *_: (self.dismiss(), self._on_edit()))
        btn_del.bind(on_release=lambda *_: (self.dismiss(), self._on_delete()))
        btn_close.bind(on_release=lambda *_: self.dismiss())

        self._render()

    def _step(self, d: int) -> None:
        if not self._images:
            return
        self._idx = (self._idx + d) % len(self._images)
        self._render()

    def _render(self) -> None:
        if not self._images:
            self._img.texture = None
            self._info.text = "0 / 0"
            return
        self._img.texture = self._b64_to_texture(self._images[self._idx])
        if self._img.texture is None:
            self._info.text = f"{self._idx + 1} / {len(self._images)} (invalid image)"
            if self._idx not in self._invalid_notified:
                self._invalid_notified.add(self._idx)
                notify(
                    title="Image Error",
                    message="This image cannot be displayed.",
                    level="warning",
                    auto_close_s=2.0,
                )
            return

        self._info.text = f"{self._idx + 1} / {len(self._images)}"

    @staticmethod
    def _b64_to_texture(b64: str):
        try:
            raw = base64.b64decode(b64)
        except Exception:
            return None
        buf = BytesIO(raw)

        for ext in ("png", "jpg", "jpeg", "webp"):
            try:
                img = CoreImage(buf, ext=ext)
                return img.texture
            except Exception:
                buf.seek(0)
        return None
