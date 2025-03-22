"""Amplitude analytics integration."""

import json
import io
import zipfile
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console
from rich.table import Table

from testgenesis_dsl import Action, TestFlow
from testgenesis_dsl.generators import playwright, cypress, generate_test_code


console = Console()


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
    console.print(f"Fetching events from Amplitude ({region} region) for {start_date.date()} to {end_date.date()}...")
    response = requests.get(
        endpoint,
        params={"start": start_str, "end": end_str},
        auth=(api_key, secret_key),
        stream=True
    )
    
    # Check for errors
    if response.status_code == 404:
        console.print("[yellow]No data available for the time range requested.[/yellow]")
        return []
    elif response.status_code == 400:
        console.print("[red]The file size of the exported data is too large. Try shortening the time range.[/red]")
        response.raise_for_status()
    elif response.status_code == 403:
        console.print("[red]Authorization failed. Check your API key, secret key, and ensure you're using the correct region (EU or standard).[/red]")
        response.raise_for_status()
    elif response.status_code == 504:
        console.print("[red]The amount of data is large causing a timeout. Use a shorter time range.[/red]")
        response.raise_for_status()
    elif response.status_code != 200:
        console.print(f"[red]Error from Amplitude API: {response.status_code} - {response.text}[/red]")
        response.raise_for_status()
    
    # Process the ZIP file response
    events = []
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        console.print(f"Processing {len(zip_file.namelist())} event files...")
        for file_name in zip_file.namelist():
            with zip_file.open(file_name) as file:
                for line in file:
                    event = json.loads(line)
                    events.append(event)
    
    console.print(f"Found {len(events)} events.")
    
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
    
    # Find common flows (simplified for example)
    flows: List[TestFlow] = []
    for session_id, session_events in sessions.items():
        if len(session_events) >= min_frequency:
            flow = create_test_flow(session_events, f"user_flow_{session_id}")
            flows.append(flow)
    
    console.print(f"Extracted {len(flows)} test flows.")
    
    # Save flows if output directory is specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for flow in flows:
            flow_path = output_dir / f"{flow.name}.json"
            flow.save(flow_path)
            console.print(f"Saved flow to {flow_path}")
    
    return flows


def get_yesterday() -> datetime:
    """Get yesterday's date at 00:00:00."""
    return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)


def get_today() -> datetime:
    """Get today's date at 23:59:59."""
    return datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)


@click.group()
def amplitude() -> None:
    """Commands for working with Amplitude analytics."""
    pass


@amplitude.command()
@click.option("--api-key", required=True, help="Amplitude API key")
@click.option("--secret-key", required=True, help="Amplitude secret key")
@click.option("--start-date", type=click.DateTime(), help="Start date (YYYY-MM-DD), defaults to yesterday")
@click.option("--end-date", type=click.DateTime(), help="End date (YYYY-MM-DD), defaults to today")
@click.option("--min-frequency", default=5, help="Minimum frequency to consider a flow")
@click.option("--output-dir", type=click.Path(), help="Directory to save extracted flows")
@click.option("--region", default="eu", help="Amplitude region (eu or standard)")
def extract_flows(
    api_key: str,
    secret_key: str,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    min_frequency: int,
    output_dir: Optional[str],
    region: str,
) -> None:
    """Extract common user flows from Amplitude analytics."""
    # Use yesterday if start_date is not provided
    if start_date is None:
        start_date = get_yesterday()
        console.print(f"[yellow]No start date provided. Using yesterday: {start_date.strftime('%Y-%m-%d')}[/yellow]")
    
    # Use today if end_date is not provided
    if end_date is None:
        end_date = get_today()
        console.print(f"[yellow]No end date provided. Using today: {end_date.strftime('%Y-%m-%d')}[/yellow]")
    
    output_path = Path(output_dir) if output_dir else None
    flows = extract_user_flows(api_key, secret_key, start_date, end_date, min_frequency, output_path, region)

    # Display results
    table = Table(title="Extracted Test Flows")
    table.add_column("Flow Name")
    table.add_column("Actions")
    table.add_column("Output Path")

    for flow in flows:
        table.add_row(
            flow.name,
            str(len(flow.actions)),
            str(output_path / f"{flow.name}.json") if output_path else "Not saved",
        )

    console.print(table)
