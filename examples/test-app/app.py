from nicegui import ui
from views.auth import create_login_page, create_register_page
from views.store import create_store_page, create_cart_page
from views.profile import create_profile_page
from lib.auth import User
from lib.amplitude import track_event
import os
from dotenv import load_dotenv

load_dotenv()

# Global state for the current user
current_user: User | None = None

def add_amplitude_tracking():
    """Add Amplitude tracking script to the page."""
    ui.add_body_html('''
    <script src="https://cdn.eu.amplitude.com/script/da0e05f882b7795f28eaba07890d418d.js"></script>
    <script>
        window.amplitude.add(window.sessionReplay.plugin({sampleRate: 1}));
        window.amplitude.init('da0e05f882b7795f28eaba07890d418d', {
            "fetchRemoteConfig":true,
            "serverZone":"EU",
            "autocapture":true
        });
    </script>
    ''')

def set_current_user(user: User | None):
    """Set the current user globally."""
    global current_user
    current_user = user
    print(f"Global current_user set to: {current_user.username if current_user else None}")

@ui.page('/')
def index():
    """Redirect to login page."""
    add_amplitude_tracking()
    print("Index page accessed")
    if current_user:
        print(f"Index: Redirecting logged in user {current_user.username} to store")
        ui.navigate.to('/store')
    else:
        print("Index: No user, redirecting to login")
        ui.navigate.to('/login')

@ui.page('/login')
def login():
    """Login page."""
    add_amplitude_tracking()
    print("Login page accessed")
    if current_user:
        print(f"Login: Already logged in as {current_user.username}, redirecting to store")
        ui.navigate.to('/store')
        return

    track_event('page_view', None, {'page': 'login'})
    create_login_page(set_current_user)

@ui.page('/register')
def register():
    """Registration page."""
    add_amplitude_tracking()
    print("Register page accessed")
    if current_user:
        print(f"Register: Already logged in as {current_user.username}, redirecting to store")
        ui.navigate.to('/store')
        return

    track_event('page_view', None, {'page': 'register'})
    create_register_page()

@ui.page('/store')
def store():
    """Store page."""
    add_amplitude_tracking()
    print("Store page accessed")
    print(f"Store: Current user is: {current_user.username if current_user else None}")
    if not current_user:
        print("Store: No user found, redirecting to login")
        ui.navigate.to('/login')
        return

    print(f"Store: Creating store page for user {current_user.username}")
    create_store_page(current_user.user_id)

@ui.page('/cart')
def cart():
    """Cart page."""
    add_amplitude_tracking()
    if not current_user:
        ui.navigate.to('/login')
        return

    create_cart_page(current_user.user_id)

@ui.page('/profile')
def profile():
    """Profile page."""
    add_amplitude_tracking()
    if not current_user:
        ui.navigate.to('/login')
        return

    create_profile_page(current_user)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='TestGenesis Test App',
        favicon='🛍️',
        dark=True,
        reload=False,  # Disable auto-reload to prevent state resets
        port=8050,
    )
