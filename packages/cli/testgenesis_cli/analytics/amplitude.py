"""Amplitude analytics integration."""

import json
import io
import zipfile
import gzip
import requests
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
from rich.console import Console
from rich.table import Table

from testgenesis_dsl import Action, TestFlow
from testgenesis_dsl.generators import playwright, cypress, generate_test_code
from .scorer import FlowScorer, save_config


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
        file_list = zip_file.namelist()
        console.print(f"Processing {len(file_list)} event files...")

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
                        console.print(f"[yellow]Warning: Error decompressing file {file_name}: {e}[/yellow]")
                        # Fall back to reading file directly
                        file.seek(0)
                        lines = file.readlines()

                    for line in lines:
                        if isinstance(line, bytes):
                            try:
                                line = line.decode('utf-8')
                            except UnicodeDecodeError:
                                console.print(f"[yellow]Warning: Cannot decode line as UTF-8, skipping.[/yellow]")
                                continue
                        if line.strip():  # Skip empty lines
                            try:
                                event = json.loads(line)
                                events.append(event)
                            except json.JSONDecodeError as e:
                                console.print(f"[yellow]Warning: Invalid JSON format: {e}[/yellow]")
                                continue
                except Exception as e:
                    console.print(f"[yellow]Warning: Error processing file {file_name}: {e}[/yellow]")
                    continue

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


@amplitude.group()
def config() -> None:
    """Manage flow scoring configuration."""
    pass

@config.command()
@click.option("--weight-name", type=click.Choice(["error_weight", "business_weight"]), required=True)
@click.option("--value", type=float, required=True)
@click.option("--config-path", default="config.yaml", help="Path to configuration file")
def set_weight(weight_name: str, value: float, config_path: str) -> None:
    """Set a weight value in the configuration."""
    scorer = FlowScorer(config_path)
    scorer.weights[weight_name] = value
    save_config(scorer.config, config_path)
    console.print(f"[green]Updated {weight_name} to {value}[/green]")

@config.command()
@click.option("--page", required=True)
@click.option("--value", type=float, required=True)
@click.option("--config-path", default="config.yaml", help="Path to configuration file")
def set_criticality(page: str, value: float, config_path: str) -> None:
    """Set business criticality for a page."""
    scorer = FlowScorer(config_path)
    scorer.business_criticality[page.lower()] = value
    save_config(scorer.config, config_path)
    console.print(f"[green]Updated criticality for {page} to {value}[/green]")

@config.command()
@click.option("--config-path", default="config.yaml", help="Path to configuration file")
def show(config_path: str) -> None:
    """Show current configuration."""
    scorer = FlowScorer(config_path)
    console.print(yaml.dump(scorer.config, default_flow_style=False))

@amplitude.command()
@click.option("--flows-dir", type=click.Path(exists=True), required=True, help="Directory containing flow files")
@click.option("--config-path", default="config.yaml", help="Path to configuration file")
@click.option("--output", type=click.Path(), help="Output file for scores (JSON)")
def score_flows(flows_dir: str, config_path: str, output: Optional[str]) -> None:
    """Score user flows based on frequency, errors, and business criticality."""
    scorer = FlowScorer(config_path)
    flows_dir = Path(flows_dir)
    results = []

    for flow_file in flows_dir.glob("user_flow_*.json"):
        with open(flow_file, 'r') as f:
            flow = json.load(f)
            score = scorer.calculate_score(flow)
            results.append({
                "flow_file": flow_file.name,
                **score
            })

    # Sort results by score in descending order
    results.sort(key=lambda x: x["score"], reverse=True)

    if output:
        with open(output, 'w') as f:
            json.dump(results, f, indent=2)
        console.print(f"[green]Saved scores to {output}[/green]")
    else:
        # Display results in a table
        table = Table(title="Flow Scores")
        table.add_column("Flow File")
        table.add_column("Score")
        table.add_column("Frequency")
        table.add_column("Errors")
        table.add_column("Criticality")

        for result in results:
            table.add_row(
                result["flow_file"],
                f"{result['score']:.2f}",
                str(result["frequency"]),
                str(result["error_count"]),
                f"{result['business_criticality']:.1f}"
            )

        console.print(table)
