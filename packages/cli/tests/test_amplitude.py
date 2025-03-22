"""Tests for Amplitude analytics integration."""

from datetime import datetime
import json
import io
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from click.testing import CliRunner

from testgenesis_cli.analytics.amplitude import amplitude, create_test_flow, get_yesterday, get_today


@pytest.fixture
def mock_amplitude_events():
    """Create mock Amplitude events."""
    event1 = {
        "user_id": "user123",
        "session_id": "session1",
        "event_type": "navigation",
        "event_properties": {"path": "/login"},
        "client_event_time": "2024-03-01T12:00:00.000Z"
    }

    event2 = {
        "user_id": "user123",
        "session_id": "session1",
        "event_type": "form",
        "event_properties": {
            "target": "#login-form",
            "data": {"username": "testuser", "password": "password123"}
        },
        "client_event_time": "2024-03-01T12:01:00.000Z"
    }

    return [event1, event2]


def test_create_test_flow(mock_amplitude_events):
    """Test converting Amplitude events to a test flow."""
    flow = create_test_flow(mock_amplitude_events, name="user_journey_user123")

    assert flow.name == "user_journey_user123"
    assert len(flow.actions) == 2

    assert flow.actions[0].type == "navigation"
    assert flow.actions[0].target == "/login"
    assert flow.actions[0].data == {"path": "/login"}

    assert flow.actions[1].type == "form"
    assert flow.actions[1].target == "#login-form"
    assert flow.actions[1].data == {"username": "testuser", "password": "password123"}


def test_get_yesterday():
    """Test the get_yesterday function returns a date one day in the past."""
    yesterday = get_yesterday()
    now = datetime.now()
    
    # Check that it's yesterday
    assert (now.date() - yesterday.date()).days == 1
    
    # Check that time is set to midnight
    assert yesterday.hour == 0
    assert yesterday.minute == 0
    assert yesterday.second == 0
    assert yesterday.microsecond == 0


def test_get_today():
    """Test the get_today function returns today's date at end of day."""
    today = get_today()
    now = datetime.now()
    
    # Check that it's today
    assert today.date() == now.date()
    
    # Check that time is set to end of day
    assert today.hour == 23
    assert today.minute == 59
    assert today.second == 59
    assert today.microsecond == 999999


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows(mock_requests_get, tmp_path, mock_amplitude_events):
    """Test extracting flows from Amplitude."""
    # Create a mock ZIP file with Amplitude data
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        zip_file.writestr("events.json", event_data)
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response

    # Run command
    runner = CliRunner()
    output_dir = tmp_path / "test_flows"

    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--start-date",
            "2024-03-01",
            "--end-date",
            "2024-03-31",
            "--min-frequency",
            "1",
            "--output-dir",
            str(output_dir),
            "--region",
            "eu",
        ],
    )

    assert result.exit_code == 0
    assert output_dir.exists()

    # Verify the API call
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    assert kwargs["params"]["start"] == "20240301T00"
    assert kwargs["params"]["end"] == "20240331T23"
    assert kwargs["auth"] == ("test-key", "test-secret")
    assert args[0] == "https://analytics.eu.amplitude.com/api/2/export"

    # Check generated flow file
    flow_files = list(output_dir.glob("*.json"))
    assert len(flow_files) == 1

    flow_data = json.loads(flow_files[0].read_text())
    assert flow_data["name"] == "user_flow_session1"
    assert len(flow_data["actions"]) == 2
    assert flow_data["actions"][0]["type"] == "navigation"
    assert flow_data["actions"][0]["target"] == "/login"
    assert flow_data["actions"][1]["type"] == "form"
    assert flow_data["actions"][1]["target"] == "#login-form"


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows_standard_region(mock_requests_get, tmp_path, mock_amplitude_events):
    """Test extracting flows from Amplitude with standard region."""
    # Create a mock ZIP file with Amplitude data
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        zip_file.writestr("events.json", event_data)
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response

    # Run command
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_standard"

    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--start-date",
            "2024-03-01",
            "--end-date",
            "2024-03-31",
            "--min-frequency",
            "1",
            "--output-dir",
            str(output_dir),
            "--region",
            "standard",
        ],
    )

    assert result.exit_code == 0
    assert output_dir.exists()

    # Verify the API call uses the standard endpoint
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    assert args[0] == "https://amplitude.com/api/2/export"


@patch("testgenesis_cli.analytics.amplitude.requests.get")
@patch("testgenesis_cli.analytics.amplitude.get_yesterday")
def test_extract_flows_default_start_date(mock_get_yesterday, mock_requests_get, tmp_path, mock_amplitude_events):
    """Test extracting flows from Amplitude with default start date."""
    # Mock yesterday's date
    yesterday = datetime(2024, 3, 15, 0, 0, 0)
    mock_get_yesterday.return_value = yesterday
    
    # Create a mock ZIP file with Amplitude data
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        zip_file.writestr("events.json", event_data)
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response
    
    # Run command without start-date
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_default"
    
    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--end-date",
            "2024-03-16",
            "--min-frequency",
            "1",
            "--output-dir",
            str(output_dir),
        ],
    )
    
    assert result.exit_code == 0
    assert "Using yesterday: 2024-03-15" in result.output
    assert output_dir.exists()
    
    # Verify that get_yesterday was called
    mock_get_yesterday.assert_called_once()
    
    # Verify that the API was called with the correct start date
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    assert kwargs["params"]["start"] == "20240315T00"
    assert args[0] == "https://analytics.eu.amplitude.com/api/2/export"


@patch("testgenesis_cli.analytics.amplitude.requests.get")
@patch("testgenesis_cli.analytics.amplitude.get_today")
def test_extract_flows_default_end_date(mock_get_today, mock_requests_get, tmp_path, mock_amplitude_events):
    """Test extracting flows from Amplitude with default end date."""
    # Mock today's date
    today = datetime(2024, 3, 16, 23, 59, 59, 999999)
    mock_get_today.return_value = today
    
    # Create a mock ZIP file with Amplitude data
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        zip_file.writestr("events.json", event_data)
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response
    
    # Run command without end-date
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_default_end"
    
    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--start-date",
            "2024-03-15",
            "--min-frequency",
            "1",
            "--output-dir",
            str(output_dir),
        ],
    )
    
    assert result.exit_code == 0
    assert "Using today: 2024-03-16" in result.output
    assert output_dir.exists()
    
    # Verify that get_today was called
    mock_get_today.assert_called_once()
    
    # Verify that the API was called with the correct end date
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    assert kwargs["params"]["end"] == "20240316T23"
    assert args[0] == "https://analytics.eu.amplitude.com/api/2/export"


@patch("testgenesis_cli.analytics.amplitude.requests.get")
@patch("testgenesis_cli.analytics.amplitude.get_yesterday")
@patch("testgenesis_cli.analytics.amplitude.get_today")
def test_extract_flows_default_both_dates(mock_get_today, mock_get_yesterday, mock_requests_get, tmp_path, mock_amplitude_events):
    """Test extracting flows from Amplitude with both default dates."""
    # Mock dates
    yesterday = datetime(2024, 3, 15, 0, 0, 0)
    today = datetime(2024, 3, 16, 23, 59, 59, 999999)
    mock_get_yesterday.return_value = yesterday
    mock_get_today.return_value = today
    
    # Create a mock ZIP file with Amplitude data
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        zip_file.writestr("events.json", event_data)
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response
    
    # Run command without both dates
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_default_both"
    
    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--min-frequency",
            "1",
            "--output-dir",
            str(output_dir),
        ],
    )
    
    assert result.exit_code == 0
    assert "Using yesterday: 2024-03-15" in result.output
    assert "Using today: 2024-03-16" in result.output
    assert output_dir.exists()
    
    # Verify that both helper functions were called
    mock_get_yesterday.assert_called_once()
    mock_get_today.assert_called_once()
    
    # Verify that the API was called with the correct dates
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    assert kwargs["params"]["start"] == "20240315T00"
    assert kwargs["params"]["end"] == "20240316T23"
    assert args[0] == "https://analytics.eu.amplitude.com/api/2/export"


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows_api_errors(mock_requests_get, tmp_path):
    """Test handling of API errors."""
    # Test 404 error
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response
    
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_error"
    
    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--start-date",
            "2024-03-01",
            "--end-date",
            "2024-03-02",
            "--output-dir",
            str(output_dir),
        ],
    )
    
    assert result.exit_code == 0
    assert "No data available" in result.output
    
    # Test 403 error
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = Exception("Forbidden")
    
    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--start-date",
            "2024-03-01",
            "--end-date",
            "2024-03-02",
            "--output-dir",
            str(output_dir),
        ],
    )
    
    assert result.exit_code != 0
    assert "Authorization failed" in result.output
    
    # Test 400 error
    mock_response.status_code = 400
    mock_response.raise_for_status.side_effect = Exception("Bad request")
    
    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--start-date",
            "2024-03-01",
            "--end-date",
            "2024-03-02",
            "--output-dir",
            str(output_dir),
        ],
    )
    
    assert result.exit_code != 0
    assert "file size of the exported data is too large" in result.output


def test_extract_flows_invalid_dates():
    """Test handling of invalid date inputs."""
    runner = CliRunner()
    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--secret-key",
            "test-secret",
            "--start-date",
            "invalid-date",
            "--end-date",
            "2024-03-31",
        ],
    )

    assert result.exit_code != 0
    assert "Error" in result.output
