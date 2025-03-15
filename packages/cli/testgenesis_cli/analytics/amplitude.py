"""Amplitude analytics integration."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from amplitude import Amplitude, BaseEvent
from rich.console import Console
from rich.table import Table

from testgenesis_dsl import Action, TestFlow
from testgenesis_dsl.generators import playwright, cypress, generate_test_code


console = Console()


def create_test_flow(events: List[BaseEvent], name: str) -> TestFlow:
    """Create a test flow from a sequence of Amplitude events."""
    actions: List[Action] = []
    for event in events:
        action = Action(
            type=event.event_type,
            target=event.event_properties.get("target", ""),
            data=event.event_properties,
        )
        actions.append(action)

    return TestFlow(name=name, actions=actions)


def extract_user_flows(
    api_key: str,
    start_date: datetime,
    end_date: datetime,
    min_frequency: int = 5,
    output_dir: Optional[Path] = None,
) -> List[TestFlow]:
    """Extract common user flows from Amplitude analytics."""
    client = Amplitude(api_key)

    # Get events for the specified date range
    events = client.get_events(
        start=start_date,
        end=end_date,
        limit=1000,  # Adjust as needed
    )

    # Group events by session
    sessions: Dict[str, List[BaseEvent]] = {}
    for event in events:
        session_id = event.session_id
        if session_id not in sessions:
            sessions[session_id] = []
        sessions[session_id].append(event)

    # Sort sessions by timestamp
    for session_id in sessions:
        sessions[session_id].sort(key=lambda e: e.timestamp)

    # Find common flows (simplified for example)
    flows: List[TestFlow] = []
    for session_id, events in sessions.items():
        if len(events) >= min_frequency:
            flow = create_test_flow(events, f"user_flow_{session_id}")
            flows.append(flow)

    # Save flows if output directory is specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for flow in flows:
            flow_path = output_dir / f"{flow.name}.json"
            flow.save(flow_path)

    return flows


@click.group()
def amplitude() -> None:
    """Commands for working with Amplitude analytics."""
    pass


@amplitude.command()
@click.option("--api-key", required=True, help="Amplitude API key")
@click.option("--start-date", required=True, type=click.DateTime(), help="Start date (YYYY-MM-DD)")
@click.option("--end-date", required=True, type=click.DateTime(), help="End date (YYYY-MM-DD)")
@click.option("--min-frequency", default=5, help="Minimum frequency to consider a flow")
@click.option("--output-dir", type=click.Path(), help="Directory to save extracted flows")
def extract_flows(
    api_key: str,
    start_date: datetime,
    end_date: datetime,
    min_frequency: int,
    output_dir: Optional[str],
) -> None:
    """Extract common user flows from Amplitude analytics."""
    output_path = Path(output_dir) if output_dir else None
    flows = extract_user_flows(api_key, start_date, end_date, min_frequency, output_path)

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
