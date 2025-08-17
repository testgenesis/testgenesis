"""Amplitude analytics integration."""

import gzip
import io
import json
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import click
import requests
import yaml
from rich.console import Console
from rich.table import Table
from testgenesis_core.analytics.amplitude import create_test_flow

from testgenesis_dsl import TestFlow

from .scorer import FlowScorer, get_default_config

console = Console()


def extract_user_flows(
    api_key: str,
    secret_key: str,
    start_date: datetime,
    end_date: datetime,
    min_frequency: int = 5,
    output_dir: Path | None = None,
    region: str = "eu",
) -> list[TestFlow]:
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
    console.print(
        f"Fetching events from Amplitude ({region} region) for {start_date.date()} to {end_date.date()}..."
    )
    response = requests.get(
        endpoint,
        params={"start": start_str, "end": end_str},
        auth=(api_key, secret_key),
        stream=True,
    )

    # Check for errors
    if response.status_code == 404:
        console.print("[yellow]No data available for the time range requested.[/yellow]")
        return []
    elif response.status_code == 400:
        console.print(
            "[red]The file size of the exported data is too large. Try shortening the time range.[/red]"
        )
        response.raise_for_status()
    elif response.status_code == 403:
        console.print(
            "[red]Authorization failed. Check your API key, secret key, and ensure you're using the correct region (EU or standard).[/red]"
        )
        response.raise_for_status()
    elif response.status_code == 504:
        console.print(
            "[red]The amount of data is large causing a timeout. Use a shorter time range.[/red]"
        )
        response.raise_for_status()
    elif response.status_code != 200:
        console.print(
            f"[red]Error from Amplitude API: {response.status_code} - {response.text}[/red]"
        )
        response.raise_for_status()

    # Process the ZIP file response
    events = []
    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
        file_list = zip_file.namelist()
        console.print(f"Processing {len(file_list)} event files from ZIP archive:")
        for file_name in file_list:
            console.print(f"  - {file_name}")

        for file_name in file_list:
            # Check if the file is a gzip file by name
            is_gzip_by_name = file_name.endswith(".gz")
            console.print(f"Processing file: {file_name} (gzipped: {is_gzip_by_name})")

            with zip_file.open(file_name) as file:
                try:
                    # Try to decompress if gzipped
                    try:
                        # Check if the file content is gzipped
                        file_content = file.read()

                        # Process based on whether it's a gzip file by name or content
                        if is_gzip_by_name or file_content.startswith(
                            b"\x1f\x8b"
                        ):  # gzip magic number
                            # Decompress gzip content
                            with io.BytesIO(file_content) as compressed_stream:
                                with gzip.GzipFile(fileobj=compressed_stream) as gzip_stream:
                                    decompressed_content = gzip_stream.read()
                            lines = decompressed_content.splitlines()
                        else:
                            lines = file_content.splitlines()
                    except Exception as e:
                        console.print(
                            f"[yellow]Warning: Error decompressing file {file_name}: {e}[/yellow]"
                        )
                        # Fall back to reading file directly
                        file.seek(0)
                        lines = file.readlines()

                    for line_raw in lines:
                        # Convert bytes to string if needed
                        if isinstance(line_raw, bytes):
                            try:
                                line = line_raw.decode("utf-8")
                            except UnicodeDecodeError:
                                console.print(
                                    "[yellow]Warning: Cannot decode line as UTF-8, skipping.[/yellow]"
                                )
                                continue
                        else:
                            line = line_raw
                        if line.strip():  # Skip empty lines
                            try:
                                event = json.loads(line)
                                events.append(event)
                            except json.JSONDecodeError as e:
                                console.print(f"[yellow]Warning: Invalid JSON format: {e}[/yellow]")
                                continue
                except Exception as e:
                    console.print(
                        f"[yellow]Warning: Error processing file {file_name}: {e}[/yellow]"
                    )
                    continue

    console.print(f"Found {len(events)} events.")

    # Group events by session
    sessions: dict[str, list[dict[str, Any]]] = {}
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
    flows: list[TestFlow] = []
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
@click.option(
    "--start-date", type=click.DateTime(), help="Start date (YYYY-MM-DD), defaults to yesterday"
)
@click.option("--end-date", type=click.DateTime(), help="End date (YYYY-MM-DD), defaults to today")
@click.option("--min-frequency", default=5, help="Minimum frequency to consider a flow")
@click.option("--output-dir", type=click.Path(), help="Directory to save extracted flows")
@click.option("--region", default="eu", help="Amplitude region (eu or standard)")
def extract_flows(
    api_key: str,
    secret_key: str,
    start_date: datetime | None,
    end_date: datetime | None,
    min_frequency: int,
    output_dir: str | None,
    region: str,
) -> None:
    """Extract common user flows from Amplitude analytics."""
    # Use yesterday if start_date is not provided
    if start_date is None:
        start_date = get_yesterday()
        console.print(
            f"[yellow]No start date provided. Using yesterday: {start_date.strftime('%Y-%m-%d')}[/yellow]"
        )

    # Use today if end_date is not provided
    if end_date is None:
        end_date = get_today()
        console.print(
            f"[yellow]No end date provided. Using today: {end_date.strftime('%Y-%m-%d')}[/yellow]"
        )

    output_path = Path(output_dir) if output_dir else None
    flows = extract_user_flows(
        api_key, secret_key, start_date, end_date, min_frequency, output_path, region
    )

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
    """Manage configuration for flow scoring."""
    pass


@config.command()
@click.option(
    "--config-path",
    type=click.Path(dir_okay=False),
    default="testgenesis.config",
    help="Path to configuration file (default: testgenesis.config)",
)
def show(config_path: str) -> None:
    """Show current configuration."""
    try:
        # Create default config if file doesn't exist
        config_file_path = Path(config_path)
        if not config_file_path.exists():
            config_data = get_default_config()
            # Ensure parent directory exists
            config_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
            click.echo(f"Created default configuration at {config_file_path}")
            click.echo(
                "Please edit the configuration file to customize weights and criticality values."
            )
        else:
            with open(config_file_path) as f:
                config_data = yaml.safe_load(f)

        # Print config as formatted YAML
        click.echo(yaml.dump(config_data, default_flow_style=False))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@config.command()
@click.option(
    "--config-path",
    type=click.Path(dir_okay=False),
    default="testgenesis.config",
    help="Path to configuration file (default: testgenesis.config)",
)
@click.option(
    "--weight-name",
    type=click.Choice(["error_weight", "business_weight"]),
    required=True,
    help="Name of the weight to update",
)
@click.option(
    "--value",
    type=float,
    required=True,
    help="New value for the weight",
)
def set_weight(config_path: str, weight_name: str, value: float) -> None:
    """Update a weight in the configuration."""
    try:
        # Load existing config or create default
        config_file_path = Path(config_path)
        if not config_file_path.exists():
            config_data = get_default_config()
            config_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
        else:
            with open(config_file_path) as f:
                config_data = yaml.safe_load(f)

        # Update the weight
        config_data["weights"][weight_name] = value

        # Save updated config
        with open(config_file_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)

        click.echo(f"Updated {weight_name} to {value}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@config.command()
@click.option(
    "--config-path",
    type=click.Path(dir_okay=False),
    default="testgenesis.config",
    help="Path to configuration file (default: testgenesis.config)",
)
@click.option(
    "--page",
    required=True,
    help="Page URL to update impact for",
)
@click.option(
    "--value",
    type=float,
    required=True,
    help="New impact value for the page",
)
def set_impact(config_path: str, page: str, value: float) -> None:
    """Update business impact for a specific page."""
    try:
        # Load existing config or create default
        config_file_path = Path(config_path)
        if not config_file_path.exists():
            config_data = get_default_config()
            config_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
        else:
            with open(config_file_path) as f:
                config_data = yaml.safe_load(f)

        # Update the impact
        page_name = page.split("/")[-1].lower()
        config_data["business_impact"][page_name] = value

        # Save updated config
        with open(config_file_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False)

        click.echo(f"Updated impact for {page_name} to {value}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@amplitude.command()
@click.option(
    "--flows-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=True,
    help="Directory containing flow files to score",
)
@click.option(
    "--config-path",
    type=click.Path(dir_okay=False),
    default="testgenesis.config",
    help="Path to configuration file (default: testgenesis.config)",
)
@click.option(
    "--output",
    type=click.Path(dir_okay=False),
    help="Path to save scores as JSON",
)
def score_flows(flows_dir: str, config_path: str, output: str | None = None) -> None:
    """Score user flows based on frequency, errors, and business impact."""
    try:
        # Debug: Print config file path
        click.echo(f"\nDebug: Using config file: {config_path}")

        # Initialize scorer with flows directory for config generation
        scorer = FlowScorer(config_path, flows_dir)

        # Debug: Print scorer configuration
        click.echo("\nDebug: Scorer Configuration:")
        click.echo(f"Weights: {scorer.weights}")
        click.echo(f"Business Impact: {scorer.business_impact}")

        # Score all flows in the directory
        results = []
        for flow_file in Path(flows_dir).glob("*.json"):
            try:
                click.echo(f"\nDebug: Processing flow file: {flow_file}")
                with open(flow_file) as f:
                    flow = json.load(f)

                # Debug: Print flow data
                click.echo("Debug: Flow Data:")
                click.echo(f"Name: {flow.get('name', 'unnamed')}")
                click.echo(f"Frequency: {flow.get('frequency', 0)}")
                click.echo(f"Actions: {len(flow.get('actions', []))}")

                result = scorer.calculate_score(flow)

                # Debug: Print scoring result
                click.echo("\nDebug: Scoring Result:")
                click.echo(f"Score: {result.get('score', 'N/A')}")
                click.echo(f"Frequency: {result.get('frequency', 'N/A')}")
                click.echo(f"Expected Errors: {result.get('expected_error_count', 'N/A')}")
                click.echo(f"Unexpected Errors: {result.get('unexpected_error_count', 'N/A')}")
                click.echo(f"Business Impact: {result.get('business_impact', 'N/A')}")
                click.echo(f"All Keys: {list(result.keys())}")

                result["flow_file"] = flow_file.name
                results.append(result)
            except Exception as e:
                click.echo(f"Warning: Error processing {flow_file}: {e}", err=True)
                continue

        # Sort results by score
        results.sort(key=lambda x: x["score"], reverse=True)

        if output:
            # Save results to file
            with open(output, "w") as f:
                json.dump(results, f, indent=2)
            click.echo(f"Saved scores to {output}")
        else:
            # Display results in a table
            table = Table(title="Flow Scores")
            table.add_column("Flow File", style="cyan")
            table.add_column("Score", justify="right", style="green")
            table.add_column("Frequency", justify="right")
            table.add_column("Errors", justify="right", style="red")
            table.add_column("Impact", justify="right")

            for result in results:
                table.add_row(
                    result["flow_file"],
                    f"{result['score']:.1f}",
                    str(result["frequency"]),
                    str(result["unexpected_error_count"]),
                    f"{result['business_impact']:.1f}",
                )

            console = Console()
            console.print(table)

            # Print detailed error information
            if any(result["error_details"] for result in results):
                console.print("\nError Details:")
                for result in results:
                    if result["error_details"]:
                        console.print(f"\nFlow: {result['flow_file']}")
                        for error in result["error_details"]:
                            if error["category"] == "unexpected":
                                console.print(f"  - {error['type']} (Unexpected)")
                                console.print(f"    Weight: {error['weight']}")
                                console.print(f"    Description: {error['description']}")
                                console.print(f"    Message: {error['message']}")
                                console.print(f"    Code: {error['error_code']}")
                                console.print(f"    Type: {error['error_type']}")
                                console.print(f"    Page: {error['page']}")
                                console.print(f"    Time: {error['timestamp']}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
