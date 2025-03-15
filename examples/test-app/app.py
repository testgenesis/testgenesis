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

@ui.page('/')
def index():
    """Redirect to login page."""
    ui.navigate.to('/login')

@ui.page('/login')
def login():
    """Login page."""
    if current_user:
        ui.navigate.to('/store')
        return
    
    track_event('page_view', None, {'page': 'login'})
    create_login_page()

@ui.page('/register')
def register():
    """Registration page."""
    if current_user:
        ui.navigate.to('/store')
        return
    
    track_event('page_view', None, {'page': 'register'})
    create_register_page()

@ui.page('/store')
def store():
    """Store page."""
    if not current_user:
        ui.navigate.to('/login')
        return
    
    create_store_page(current_user.user_id)

@ui.page('/cart')
def cart():
    """Cart page."""
    if not current_user:
        ui.navigate.to('/login')
        return
    
    create_cart_page(current_user.user_id)

@ui.page('/profile')
def profile():
    """Profile page."""
    if not current_user:
        ui.navigate.to('/login')
        return
    
    create_profile_page(current_user)

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title='TestGenesis Test App',
        favicon='🛍️',
        dark=True,
        reload=True,
        port=8081,
    ) 