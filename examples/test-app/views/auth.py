from collections.abc import Callable

from lib.amplitude import track_event
from lib.auth import User, authenticate_user, register_user
from nicegui import ui


def create_login_page(set_current_user: Callable[[User | None], None]):
    """Create the login page."""
    with ui.card().classes("w-96"):
        ui.label("Login").classes("text-h6")
        username = ui.input("Username").classes("w-full")
        password = ui.input("Password", password=True).classes("w-full")

        def handle_login():
            try:
                user = authenticate_user(username.value, password.value)
                if user:
                    print(f"Login successful - User: {user.username} (ID: {user.user_id})")
                    track_event("login_success", user.user_id)
                    set_current_user(user)
                    print(f"Current user set to: {user.username}")
                    ui.navigate.to("/store")
                else:
                    track_event("login_error")
                    ui.notify("Invalid credentials", type="negative")
            except Exception as e:
                track_event("login_error")
                ui.notify(str(e), type="negative")

        # Handle Enter key press
        def on_enter(_):
            handle_login()

        username.on("keydown.enter", on_enter)
        password.on("keydown.enter", on_enter)

        ui.button("Login", on_click=handle_login).classes("w-full")
        ui.button("Register", on_click=lambda: ui.navigate.to("/register")).classes("w-full")


def create_register_page():
    """Create the registration page."""
    with ui.card().classes("w-96"):
        ui.label("Register").classes("text-h6")
        username = ui.input("Username").classes("w-full")
        password = ui.input("Password", password=True).classes("w-full")
        confirm_password = ui.input("Confirm Password", password=True).classes("w-full")

        def handle_register():
            try:
                if password.value != confirm_password.value:
                    ui.notify("Passwords do not match", type="negative")
                    return

                track_event("signup_start")
                user = register_user(username.value, password.value)
                track_event("signup_complete", user.user_id)
                ui.notify("Registration successful", type="positive")
                ui.navigate.to("/login")
            except Exception as e:
                ui.notify(str(e), type="negative")

        # Handle Enter key press
        def on_enter(_):
            handle_register()

        username.on("keydown.enter", on_enter)
        password.on("keydown.enter", on_enter)
        confirm_password.on("keydown.enter", on_enter)

        ui.button("Register", on_click=handle_register).classes("w-full")
        ui.button("Back to Login", on_click=lambda: ui.navigate.to("/login")).classes("w-full")
