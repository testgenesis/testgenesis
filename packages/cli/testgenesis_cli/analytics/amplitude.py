"""Amplitude analytics integration."""

import json
from pathlib import Path
from typing import Optional

import click
from amplitude import Amplitude, BaseEvent
from rich.console import Console
from rich.table import Table

from testgenesis_dsl.models.test_flow import TestFlow, UserAction
from testgenesis_dsl.generators import playwright, cypress


console = Console()


def create_test_flow(events: list[BaseEvent]) -> TestFlow:
    """Convert Amplitude events into a TestGenesis test flow."""
    actions = []

    for event in events:
        # Convert Amplitude event properties to test actions
        if event.event_type == "page_view":
            actions.append(
                UserAction(
                    type="navigation",
                    target=event.event_properties.get("path", "/"),
                    assertions=["url", "title"],
                )
            )
        elif event.event_type == "click":
            actions.append(
                UserAction(
                    type="click",
                    target=event.event_properties.get("element_selector"),
                    assertions=["element_visible", "element_enabled"],
                )
            )
        elif event.event_type == "form_submit":
            actions.append(
                UserAction(
                    type="form",
                    target=event.event_properties.get("form_selector"),
                    data=event.event_properties.get("form_data", {}),
                    assertions=["form_valid", "submit_success"],
                )
            )

    return TestFlow(name=f"user_journey_{events[0].user_id}", actions=actions)


@click.group()
def amplitude():
    """Amplitude analytics integration commands."""
    pass


@amplitude.command()
@click.option(
    "--api-key",
    envvar="AMPLITUDE_API_KEY",
    help="Amplitude API key (can also be set via AMPLITUDE_API_KEY env var)",
)
@click.option(
    "--start-date",
    type=click.DateTime(),
    help="Start date for event export (format: YYYY-MM-DD)",
    required=True,
)
@click.option(
    "--end-date",
    type=click.DateTime(),
    help="End date for event export (format: YYYY-MM-DD)",
    required=True,
)
@click.option(
    "--min-frequency",
    type=int,
    default=5,
    help="Minimum frequency of a user flow to be included",
)
@click.option(
    "--output-dir",
    type=click.Path(),
    default="./test_flows",
    help="Directory to save generated test flows",
)
def extract_flows(
    api_key: str,
    start_date: str,
    end_date: str,
    min_frequency: int,
    output_dir: str,
) -> None:
    """Extract common user flows from Amplitude analytics."""
    try:
        # Initialize Amplitude client
        client = Amplitude(api_key)

        # Fetch events
        events = client.export_events(
            start_time=start_date,
            end_time=end_date,
        )

        # Group events by user session
        sessions = {}
        for event in events:
            session_id = event.session_id
            if session_id not in sessions:
                sessions[session_id] = []
            sessions[session_id].append(event)

        # Convert sessions to test flows
        flows = []
        for session_events in sessions.values():
            flow = create_test_flow(session_events)
            flows.append(flow)

        # Group similar flows and count frequencies
        flow_patterns = {}
        for flow in flows:
            pattern = flow.get_pattern()
            if pattern not in flow_patterns:
                flow_patterns[pattern] = {"count": 0, "flow": flow}
            flow_patterns[pattern]["count"] += 1

        # Filter by minimum frequency
        common_flows = {
            pattern: data
            for pattern, data in flow_patterns.items()
            if data["count"] >= min_frequency
        }

        # Save flows to output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        for pattern, data in common_flows.items():
            flow = data["flow"]
            count = data["count"]

            flow_path = output_path / f"{flow.name}.json"
            with open(flow_path, "w") as f:
                json.dump(
                    {
                        "name": flow.name,
                        "frequency": count,
                        "actions": [action.dict() for action in flow.actions],
                    },
                    f,
                    indent=2,
                )

        # Display summary
        table = Table(title="Extracted Test Flows")
        table.add_column("Flow Name")
        table.add_column("Frequency")
        table.add_column("Actions")

        for pattern, data in common_flows.items():
            flow = data["flow"]
            count = data["count"]
            table.add_row(
                flow.name,
                str(count),
                str(len(flow.actions)),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()
