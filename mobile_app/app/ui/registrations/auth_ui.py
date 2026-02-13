from __future__ import annotations

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from core.registry import ui_component
from ui.layouts.auth_layout import AuthLayout
from ui.widgets.notify_popup import notify


def _support_details(ctx) -> str:
    cfg = ctx.app.state.config
    return (
        f"Support: {cfg.support_email}\n"
        f"Backend: {cfg.api_base_url}\n"
        "If login/register fails, copy these details and send them to support."
    )


@ui_component(slot=AuthLayout.HEADER, component_id="auth.hero", order=10)
def auth_hero(ctx):
    root = BoxLayout(orientation="vertical", spacing=8, size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))
    root.add_widget(Label(text="Welcome to SpotOnSight", font_size="26sp", bold=True, size_hint_y=None, height="34dp"))
    root.add_widget(
        Label(
            text="Sign in to save favorites, follow people, and share spots.",
            font_size="14sp",
            color=(0.45, 0.48, 0.50, 1),
            size_hint_y=None,
            height="24dp",
        )
    )
    return root


@ui_component(slot=AuthLayout.MAIN, component_id="auth.forms", order=10)
def auth_forms(ctx):
    auth_service = ctx.app.service("auth_service")

    root = BoxLayout(orientation="vertical", spacing=12)

    card = ctx.app.kv_factory("RoundedCard")()
    card.orientation = "vertical"
    card.spacing = 8

    login_title = Label(text="Sign In", bold=True, font_size="16sp", size_hint_y=None, height="24dp")
    login_user = TextInput(hint_text="Username or email", multiline=False, size_hint_y=None, height="42dp")
    login_pass = TextInput(hint_text="Password", password=True, multiline=False, size_hint_y=None, height="42dp")
    login_btn = ctx.app.kv_factory("PrimaryButton")()
    login_btn.text = "Login"

    card.add_widget(login_title)
    card.add_widget(login_user)
    card.add_widget(login_pass)
    card.add_widget(login_btn)

    card.add_widget(Label(text="", size_hint_y=None, height="6dp"))
    card.add_widget(Label(text="Create Account", bold=True, font_size="16sp", size_hint_y=None, height="24dp"))

    reg_username = TextInput(hint_text="Username", multiline=False, size_hint_y=None, height="42dp")
    reg_email = TextInput(hint_text="Email", multiline=False, size_hint_y=None, height="42dp")
    reg_display = TextInput(hint_text="Display name", multiline=False, size_hint_y=None, height="42dp")
    reg_pass = TextInput(hint_text="Password (min 8 chars)", password=True, multiline=False, size_hint_y=None, height="42dp")
    reg_btn = ctx.app.kv_factory("GhostButton")()
    reg_btn.text = "Register"

    card.add_widget(reg_username)
    card.add_widget(reg_email)
    card.add_widget(reg_display)
    card.add_widget(reg_pass)
    card.add_widget(reg_btn)

    def _on_login(*_):
        ok = auth_service.login(
            username_or_email=(login_user.text or "").strip(),
            password=(login_pass.text or ""),
        )
        if not ok:
            notify(
                title="Login Failed",
                message="Could not sign you in.",
                level="error",
                details=auth_service.last_error(),
            )
            return

        notify(title="Welcome", message="Signed in successfully.", level="success", auto_close_s=1.2)
        ctx.screen.go("home")

    def _on_register(*_):
        username = (reg_username.text or "").strip()
        email = (reg_email.text or "").strip()
        display_name = (reg_display.text or username).strip()
        password = (reg_pass.text or "")

        if len(password) < 8:
            notify(title="Invalid Password", message="Password must be at least 8 characters.", level="warning")
            return

        ok = auth_service.register(
            username=username,
            email=email,
            password=password,
            display_name=display_name,
        )
        if not ok:
            notify(
                title="Registration Failed",
                message="Could not create your account.",
                level="error",
                details=auth_service.last_error(),
            )
            return

        notify(title="Account Created", message="Your account is ready.", level="success", auto_close_s=1.2)
        ctx.screen.go("home")

    login_btn.bind(on_release=_on_login)
    reg_btn.bind(on_release=_on_register)

    root.add_widget(card)
    return root


@ui_component(slot=AuthLayout.FOOTER, component_id="auth.help", order=10)
def auth_help(ctx):
    root = BoxLayout(orientation="vertical", spacing=8, size_hint_y=None)
    root.bind(minimum_height=root.setter("height"))

    help_btn = ctx.app.kv_factory("GhostButton")()
    help_btn.text = "Need Help?"

    policy = Label(
        text="By continuing, you agree to Terms and Privacy Policy.",
        font_size="12sp",
        color=(0.45, 0.48, 0.50, 1),
        size_hint_y=None,
        height="18dp",
    )

    def _on_help(*_):
        notify(
            title="Support",
            message="If you cannot log in or register, contact support.",
            level="info",
            details=_support_details(ctx),
        )

    help_btn.bind(on_release=_on_help)
    root.add_widget(help_btn)
    root.add_widget(policy)
    return root
