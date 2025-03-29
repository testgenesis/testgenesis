"""Core Amplitude analytics integration."""

import json
import io
import zipfile
import gzip
import requests
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from testgenesis_dsl import Action, TestFlow
from testgenesis_dsl.generators import playwright, cypress, generate_test_code
from .scorer import FlowScorer, save_config, get_default_config


def create_test_flow(events: List[Dict[str, Any]], name: str) -> TestFlow:
    """Create a test flow from a sequence of Amplitude events."""
    actions: List[Action] = []
    for event in events:
        event_type = event.get("event_type", "")
        event_properties = event.get("event_properties", {})

        if event_type == "navigation":
            action = Action(
                type=event_type,
                target=event_properties.get("path", ""),
                data=event_properties,
            )
        elif event_type == "form":
            action = Action(
                type=event_type,
                target=event_properties.get("target", ""),
                data=event_properties.get("data", {}),
            )
        elif event_type.lower().endswith("_error") or event_type.lower().startswith("error"):
            # Handle error events
            action = Action(
                type="error",
                target=event_properties.get("target", ""),
                data=event_properties,
            )
        else:
            action = Action(
                type=event_type,
                target=event_properties.get("target", ""),
                data=event_properties,
            )
        actions.append(action)

    return TestFlow(name=name, actions=actions)


def extract_user_flows(
    api_key: str,
    secret_key: str,
    start_date: datetime,
    end_date: datetime,
    min_frequency: int = 5,
    output_dir: Optional[Path] = None,
    region: str = "eu"
) -> List[TestFlow]:
    """Extract common user flows from Amplitude analytics using the Export API."""
    # Format dates for Amplitude Export API (YYYYMMDDTHH format)
    start_str = start_date.strftime("%Y%m%dT%H")
    # For end date, always use hour 23 to cover the full day
    end_str = end_date.strftime("%Y%m%dT") + "23"

    # Set up the API endpoint based on region
    if region.lower() == "eu":
        endpoint = "https://analytics.eu.amplitude.com/api/2/export"
    else:
        endpoint = "https://amplitude.com/api/2/export"

    # Make the API request
    response = requests.get(
        endpoint,
        params={"start": start_str, "end": end_str},
        auth=(api_key, secret_key),
        stream=True
    )

    # Check for errors
    if response.status_code == 404:
        raise ValueError("No data available for the time range requested.")
    elif response.status_code == 400:
        raise ValueError("The file size of the exported data is too large. Try shortening the time range.")
    elif response.status_code == 403:
        raise ValueError("Authorization failed. Check your API key, secret key, and ensure you're using the correct region (EU or standard).")
    elif response.status_code == 504:
        raise ValueError("The amount of data is large causing a timeout. Use a shorter time range.")
    elif response.status_code != 200:
        raise ValueError(f"Error from Amplitude API: {response.status_code} - {response.text}")

    # Process the ZIP file response
    events = []
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        file_list = zip_file.namelist()

        for file_name in file_list:
            # Check if the file is a gzip file by name
            is_gzip_by_name = file_name.endswith('.gz')

            with zip_file.open(file_name) as file:
                try:
                    # Try to decompress if gzipped
                    try:
                        # Check if the file content is gzipped
                        file_content = file.read()

                        # Process based on whether it's a gzip file by name or content
                        if is_gzip_by_name or file_content.startswith(b'\x1f\x8b'):  # gzip magic number
                            # Decompress gzip content
                            with io.BytesIO(file_content) as compressed_stream:
                                with gzip.GzipFile(fileobj=compressed_stream) as gzip_stream:
                                    decompressed_content = gzip_stream.read()
                            lines = decompressed_content.splitlines()
                        else:
                            lines = file_content.splitlines()
                    except Exception as e:
                        # Fall back to reading file directly
                        file.seek(0)
                        lines = file.readlines()

                    for line in lines:
                        if isinstance(line, bytes):
                            try:
                                line = line.decode('utf-8')
                            except UnicodeDecodeError:
                                continue
                        if line.strip():  # Skip empty lines
                            try:
                                event = json.loads(line)
                                events.append(event)
                            except json.JSONDecodeError:
                                continue
                except Exception:
                    continue

    # Group events by session
    sessions: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        session_id = str(event.get("session_id", ""))  # Convert to string to be safe
        if not session_id:
            continue  # Skip events without session_id
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(event)

    # Sort sessions by timestamp
    for session_id in sessions:
        sessions[session_id].sort(key=lambda e: e.get("client_event_time", ""))

    # Find common flows
    flows: List[TestFlow] = []
    for session_id, session_events in sessions.items():
        if len(session_events) >= min_frequency:
            flow = create_test_flow(session_events, f"user_flow_{session_id}")
            flows.append(flow)

    # Save flows if output directory is specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for flow in flows:
            flow_path = output_dir / f"{flow.name}.json"
            flow.save(flow_path)

    return flows


def get_yesterday() -> datetime:
    """Get yesterday's date at 00:00:00."""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)


def get_today() -> datetime:
    """Get today's date at 23:59:59."""
    return datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999) 