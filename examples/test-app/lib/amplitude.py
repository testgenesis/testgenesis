from nicegui import ui

def track_event(event_type: str, user_id: str | None = None, event_properties: dict | None = None):
    """Track an event in Amplitude using the browser SDK."""
    try:
        # Create JavaScript code to track the event
        js_code = f'''
        if (window.amplitude) {{
            if ('{user_id}') {{
                window.amplitude.setUserId('{user_id}');
            }}
            window.amplitude.track('{event_type}', {str(event_properties or {})});
        }}
        '''
        
        # Execute the JavaScript code
        ui.run_javascript(js_code)
    except Exception as e:
        print(f"Failed to track event: {e}")  # Log error but don't crash the app 