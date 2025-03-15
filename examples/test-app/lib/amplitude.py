from amplitude import Amplitude, BaseEvent
import os
from dotenv import load_dotenv
import time

load_dotenv()

amplitude = Amplitude(os.getenv('AMPLITUDE_API_KEY'))

def track_event(event_type: str, user_id: str | None = None, event_properties: dict | None = None):
    """Track an event in Amplitude."""
    try:
        event = BaseEvent(
            event_type=event_type,
            user_id=user_id or 'anonymous',  # Amplitude requires a user_id
            device_id='test-device',  # Required by Amplitude
            event_properties=event_properties or {},
            time=int(time.time() * 1000)  # Current time in milliseconds
        )
        amplitude.track(event)
    except Exception as e:
        print(f"Failed to track event: {e}")  # Log error but don't crash the app 