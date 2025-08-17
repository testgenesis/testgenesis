from lib.amplitude import track_event
from lib.auth import User
from nicegui import ui


def create_profile_page(user: User):
    """Create the profile page."""
    track_event('page_view', user.user_id, {'page': 'profile'})

    with ui.column().classes('w-full max-w-3xl mx-auto p-4'):
        ui.label('Profile').classes('text-h4')

        with ui.card().classes('w-full'):
            ui.label('User Information').classes('text-h6')
            ui.label(f'Username: {user.username}').classes('text-body1')
            ui.label(f'User ID: {user.user_id}').classes('text-body2')

        ui.button('Back to Store', on_click=lambda: ui.navigate.to('/store')).classes('mt-4')
