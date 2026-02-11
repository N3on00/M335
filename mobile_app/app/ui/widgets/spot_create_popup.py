from __future__ import annotations

from typing import Callable, List

from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label


class SpotCreatePopup(Popup):
    """Simple popup to create a spot.

    KISS: no complex validation UI; only required title.
    """

    def __init__(self, lat: float, lon: float, on_submit: Callable[[dict], None], **kwargs):
        super().__init__(title="Neuer Spot", size_hint=(0.9, 0.8), **kwargs)
        self._on_submit = on_submit

        root = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))

        self.title_in = TextInput(hint_text="Titel (Pflicht)", multiline=False)
        self.desc_in = TextInput(hint_text="Beschreibung", multiline=True)
        self.type_in = TextInput(hint_text="Typ (z.B. chill, sport, other)", multiline=False)
        self.tags_in = TextInput(hint_text="Tags (comma separated)", multiline=False)

        root.add_widget(Label(text=f"Position: {lat:.5f}, {lon:.5f}", size_hint_y=None, height=dp(22)))
        root.add_widget(self.title_in)
        root.add_widget(self.type_in)
        root.add_widget(self.tags_in)
        root.add_widget(self.desc_in)

        bar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        btn_cancel = Button(text="Abbrechen")
        btn_create = Button(text="Erstellen")
        btn_cancel.bind(on_release=lambda *_: self.dismiss())
        btn_create.bind(on_release=lambda *_: self._submit(lat, lon))
        bar.add_widget(btn_cancel)
        bar.add_widget(btn_create)

        root.add_widget(bar)
        self.content = root

    def _submit(self, lat: float, lon: float) -> None:
        title = (self.title_in.text or "").strip()
        if not title:
            self.title_in.hint_text = "Titel fehlt!"
            return

        payload = {
            "title": title,
            "description": (self.desc_in.text or "").strip(),
            "type": (self.type_in.text or "other").strip() or "other",
            "tags": [t.strip() for t in (self.tags_in.text or "").split(",") if t.strip()],
            "lat": float(lat),
            "lon": float(lon),
        }
        self.dismiss()
        self._on_submit(payload)
