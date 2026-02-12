from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Callable, List, Optional

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput


def _parse_tags(text: str) -> List[str]:
    # Comma-separated tags, KISS
    tags = [t.strip() for t in (text or "").split(",")]
    return [t for t in tags if t]


@dataclass(frozen=True)
class SpotDraft:
    spot_id: Optional[str]
    title: str
    description: str
    tags: List[str]
    lat: float
    lon: float
    images_base64: List[str]


class SpotEditorPopup(Popup):
    """Create/Edit Spot popup.

    - No manual lat/lon typing.
    - Location is changed via "Pick location on map".
    - Images are picked only via button, not automatically.
    """

    def __init__(
        self,
        *,
        draft: SpotDraft,
        on_submit: Callable[[SpotDraft], None],
        on_pick_location: Callable[[SpotDraft], None],
        submit_label: str = "Speichern",
        **kwargs,
    ):
        super().__init__(title="Spot", size_hint=(0.94, 0.94), auto_dismiss=True, **kwargs)

        self._draft = draft
        self._on_submit = on_submit
        self._on_pick_location = on_pick_location
        self._images = list(draft.images_base64)

        root = BoxLayout(orientation="vertical", spacing=8, padding=12)

        self._title = TextInput(text=draft.title, hint_text="Titel", multiline=False, size_hint_y=None, height="40dp")
        root.add_widget(self._title)

        self._desc = TextInput(
            text=draft.description,
            hint_text="Beschreibung",
            multiline=True,
            size_hint_y=None,
            height="120dp",
        )
        root.add_widget(self._desc)

        self._tags = TextInput(
            text=", ".join(draft.tags),
            hint_text="Tags (comma separated) z.B. Nature, Quiet, Walking",
            multiline=False,
            size_hint_y=None,
            height="40dp",
        )
        root.add_widget(self._tags)

        loc_row = BoxLayout(orientation="horizontal", size_hint_y=None, height="44dp", spacing=8)
        self._loc_label = Label(text=f"Location: {draft.lat:.6f}, {draft.lon:.6f}", size_hint_x=1)
        btn_pick = Button(text="Pick on map", size_hint_x=None, width="140dp")
        loc_row.add_widget(self._loc_label)
        loc_row.add_widget(btn_pick)
        root.add_widget(loc_row)

        self._img_label = Label(text=f"Bilder: {len(self._images)} ausgewählt", size_hint_y=None, height="28dp")
        root.add_widget(self._img_label)

        btn_pick_imgs = Button(text="Bilder auswählen", size_hint_y=None, height="44dp")
        root.add_widget(btn_pick_imgs)

        actions = BoxLayout(orientation="horizontal", size_hint_y=None, height="48dp", spacing=8)
        btn_submit = Button(text=submit_label)
        btn_cancel = Button(text="Abbrechen")
        actions.add_widget(btn_submit)
        actions.add_widget(btn_cancel)
        root.add_widget(actions)

        self.content = root

        btn_pick.bind(on_release=lambda *_: self._pick_location())
        btn_pick_imgs.bind(on_release=lambda *_: self._open_filechooser())
        btn_submit.bind(on_release=lambda *_: self._submit())
        btn_cancel.bind(on_release=lambda *_: self.dismiss())

    def _pick_location(self) -> None:
        self.dismiss()
        self._on_pick_location(self._current_draft())

    def _submit(self) -> None:
        title = (self._title.text or "").strip()
        if not title:
            self.title = "Spot (Titel fehlt)"
            return

        self.dismiss()
        self._on_submit(self._current_draft())

    def _current_draft(self) -> SpotDraft:
        return SpotDraft(
            spot_id=self._draft.spot_id,
            title=(self._title.text or "").strip(),
            description=(self._desc.text or "").strip(),
            tags=_parse_tags(self._tags.text),
            lat=float(self._draft.lat),
            lon=float(self._draft.lon),
            images_base64=list(self._images),
        )

    def _open_filechooser(self) -> None:
        chooser = FileChooserIconView(filters=["*.png", "*.jpg", "*.jpeg", "*.webp"])
        pop = Popup(title="Bilder auswählen", content=chooser, size_hint=(0.9, 0.9), auto_dismiss=True)

        def on_dismiss(*_):
            sel = list(chooser.selection or [])
            if not sel:
                return
            self._images = [self._file_to_b64(p) for p in sel if p]
            self._img_label.text = f"Bilder: {len(self._images)} ausgewählt"

        pop.bind(on_dismiss=on_dismiss)
        pop.open()

    @staticmethod
    def _file_to_b64(path: str) -> str:
        with open(path, "rb") as f:
            raw = f.read()
        return base64.b64encode(raw).decode("ascii")