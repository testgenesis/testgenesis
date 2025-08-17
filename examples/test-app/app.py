import random

from dotenv import load_dotenv
from lib.amplitude import track_event
from lib.auth import User
from nicegui import ui
from views.auth import create_login_page, create_register_page
from views.checkout import create_checkout_page
from views.profile import create_profile_page
from views.store import create_cart_page, create_store_page

load_dotenv()

# Global state for the current user
current_user: User | None = None

# Simulated database
users = {
    "test@example.com": {"password": "password123", "name": "Test User"}
}

# Simulated error states
error_states = {
    "login": False,  # Database connection error
    "profile": False,  # Server error
    "checkout": False,  # Network error
}

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

@ui.page('/api/toggle-error/<flow>')
def toggle_error(flow):
    """Toggle error state for a specific flow."""
    if flow in error_states:
        error_states[flow] = not error_states[flow]
        ui.notify(f"Error state for {flow} toggled", type="success")
        return {
            "success": True,
            "flow": flow,
            "error_state": error_states[flow]
        }
    return {"error": "Invalid flow"}

@ui.page('/api/random-error')
def random_error():
    """Randomly trigger an error in one of the flows."""
    flow = random.choice(list(error_states.keys()))
    error_states[flow] = True
    ui.notify(f"Error triggered in {flow}", type="error")
    return {
        "success": True,
        "flow": flow,
        "error_state": True
    }

def create_error_control_panel():
    """Create a control panel for toggling errors."""
    with ui.card().classes('fixed top-4 right-4 z-10 bg-gray-800 p-4 rounded-lg shadow-lg'):
        ui.label('Error Control Panel').classes('text-h6 mb-4 text-white')

        # Individual error toggles
        for flow in error_states:
            with ui.row().classes('items-center gap-2 mb-2'):
                ui.label(flow.title()).classes('text-white')
                ui.switch(
                    value=error_states[flow],
                    on_change=lambda e, f=flow: toggle_error(f)
                ).classes('text-white')

        # Random error button
        ui.button(
            'Trigger Random Error',
            on_click=random_error
        ).classes('w-full mt-4 bg-red-500 hover:bg-red-600 text-white')

        # Reset all button
        ui.button(
            'Reset All Errors',
            on_click=lambda: [toggle_error(flow) for flow in error_states if error_states[flow]]
        ).classes('w-full mt-2 bg-gray-600 hover:bg-gray-700 text-white')

def create_top_navigation():
    """Create the top navigation bar."""
    with ui.header().classes('fixed top-0 left-0 right-0 z-20 bg-gray-900 text-white p-4'):
        with ui.row().classes('w-full justify-between items-center'):
            # Left side - Logo/Home
            with ui.row().classes('items-center gap-4'):
                ui.link('🛍️ TestGenesis', '/store').classes('text-xl font-bold')

            # Right side - Navigation items
            with ui.row().classes('items-center gap-4'):
                with ui.button(
                    'Menu', icon='menu'
                ).props('flat').classes('text-white') as menu_button:
                    with ui.menu().classes('bg-gray-800 text-white') as menu:
                        if current_user:
                            ui.menu_item(
                                'Store',
                                on_click=lambda: ui.navigate.to('/store')
                            ).classes('hover:bg-gray-700')
                            ui.menu_item(
                                'Cart',
                                on_click=lambda: ui.navigate.to('/cart')
                            ).classes('hover:bg-gray-700')
                            ui.menu_item(
                                'Profile',
                                on_click=lambda: ui.navigate.to('/profile')
                            ).classes('hover:bg-gray-700')
                            ui.separator().classes('my-2')
                            ui.menu_item(
                                'Logout',
                                on_click=lambda: set_current_user(None)
                            ).classes('text-red-400 hover:bg-gray-700')
                        else:
                            ui.menu_item(
                                'Login',
                                on_click=lambda: ui.navigate.to('/login')
                            ).classes('hover:bg-gray-700')
                            ui.menu_item(
                                'Register',
                                on_click=lambda: ui.navigate.to('/register')
                            ).classes('hover:bg-gray-700')

                    menu_button.on('click', menu.toggle)

@ui.page('/')
def index():
    """Redirect to login page."""
    add_amplitude_tracking()
    create_error_control_panel()
    create_top_navigation()
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
    create_error_control_panel()
    create_top_navigation()
    print("Login page accessed")
    if current_user:
        print(f"Login: Already logged in as {current_user.username}, redirecting to store")
        ui.navigate.to('/store')
        return

    track_event('page_view', None, {'page': 'login'})

    # Simulate database connection error
    if error_states["login"]:
        ui.notify(
            'Database Connection Error: Unable to connect to authentication database',
            type='error',
            position='top',
            timeout=0,  # Don't auto-dismiss
            multi_line=True,
            color='red',
            text_color='white',
            classes='bg-red-500 text-white p-4 rounded-lg shadow-lg'
        )
        track_event('error', None, {
            'error_type': 'login_error',
            'error_code': 'database_error',
            'message': 'Database connection failed',
            'details': 'Unable to connect to authentication database'
        })
        return

    create_login_page(set_current_user)

@ui.page('/register')
def register():
    """Registration page."""
    add_amplitude_tracking()
    create_error_control_panel()
    create_top_navigation()
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
    create_error_control_panel()
    create_top_navigation()
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
    create_error_control_panel()
    create_top_navigation()
    if not current_user:
        ui.navigate.to('/login')
        return

    create_cart_page(current_user.user_id)

@ui.page('/profile')
def profile():
    """Profile page."""
    add_amplitude_tracking()
    create_error_control_panel()
    create_top_navigation()
    if not current_user:
        ui.navigate.to('/login')
        return

    # Simulate server error
    if error_states["profile"]:
        ui.notify("Internal server error", type="error")
        track_event('error', None, {
            'error_type': 'server_error',
            'error_code': 'internal_server_error',
            'message': 'Internal server error',
            'details': 'Error processing profile data'
        })
        return

    create_profile_page(current_user)

@ui.page('/checkout')
def checkout():
    """Checkout page."""
    add_amplitude_tracking()
    create_error_control_panel()
    create_top_navigation()
    if not current_user:
        ui.navigate.to('/login')
        return

    # Simulate network error
    if error_states["checkout"]:
        ui.notify("Payment service unavailable", type="error")
        track_event('error', None, {
            'error_type': 'network_error',
            'error_code': 'payment_service_unavailable',
            'message': 'Payment service unavailable',
            'details': 'Unable to connect to payment gateway'
        })
        return

    create_checkout_page()

if __name__ in {"__main__", "__mp_main__"}:
    import os
    port = int(os.environ.get('PORT', 8050))
    ui.run(
        title='TestGenesis Test App',
        favicon='🛍️',
        dark=True,
        reload=False,  # Disable auto-reload to prevent state resets
        port=port,
    )
