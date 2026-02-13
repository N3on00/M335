from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup


@dataclass(frozen=True)
class NotificationAction:
    label: str
    callback: Optional[Callable[[], None]] = None


_LEVEL_STYLE = {
    "info": {"title_color": (0.16, 0.31, 0.54, 1), "text_color": (0.12, 0.16, 0.2, 1)},
    "success": {"title_color": (0.10, 0.42, 0.24, 1), "text_color": (0.11, 0.22, 0.16, 1)},
    "warning": {"title_color": (0.56, 0.34, 0.08, 1), "text_color": (0.31, 0.21, 0.09, 1)},
    "error": {"title_color": (0.58, 0.14, 0.14, 1), "text_color": (0.33, 0.12, 0.12, 1)},
}


class NotificationPopup(Popup):
    def __init__(
        self,
        *,
        title: str,
        message: str,
        level: str = "info",
        actions: Optional[Iterable[NotificationAction]] = None,
        details: Optional[str] = None,
        include_copy_details_action: bool = True,
        auto_close_s: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(title=title, size_hint=(0.78, 0.34), auto_dismiss=True, **kwargs)

        style = _LEVEL_STYLE.get(level, _LEVEL_STYLE["info"])

        root = BoxLayout(orientation="vertical", spacing=10, padding=12)
        body = Label(
            text=message,
            halign="left",
            valign="middle",
            color=style["text_color"],
        )
        body.bind(size=lambda *_: setattr(body, "text_size", body.size))
        root.add_widget(body)

        row = BoxLayout(orientation="horizontal", size_hint_y=None, height="44dp", spacing=8)
        actions_list = list(actions or [])
        details_text = (details or "").strip()
        if include_copy_details_action and details_text:
            actions_list.insert(0, NotificationAction(label="Copy details", callback=lambda: Clipboard.copy(details_text)))

        if not actions_list:
            actions_list = [NotificationAction(label="OK")]

        for act in actions_list:
            btn = Button(text=(act.label or "OK"), background_normal="", background_down="")

            def _on_release(_btn, action: NotificationAction = act):
                self.dismiss()
                if action.callback:
                    action.callback()

            btn.bind(on_release=_on_release)
            row.add_widget(btn)

        root.add_widget(row)
        self.content = root
        self.title_color = style["title_color"]

        if auto_close_s and auto_close_s > 0:
            Clock.schedule_once(lambda *_: self.dismiss(), auto_close_s)


def notify(
    *,
    title: str,
    message: str,
    level: str = "info",
    actions: Optional[Iterable[NotificationAction]] = None,
    details: Optional[str] = None,
    include_copy_details_action: bool = True,
    auto_close_s: Optional[float] = None,
) -> NotificationPopup:
    pop = NotificationPopup(
        title=title,
        message=message,
        level=level,
        actions=actions,
        details=details,
        include_copy_details_action=include_copy_details_action,
        auto_close_s=auto_close_s,
    )
    pop.open()
    return pop
