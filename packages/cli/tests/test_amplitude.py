"""Tests for Amplitude analytics integration."""

from datetime import datetime
import json
import io
import zipfile
import gzip
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from click.testing import CliRunner
from hypothesis import settings, given, strategies as st

from testgenesis_cli.analytics.amplitude import (
    amplitude, create_test_flow, get_yesterday, get_today
)
from testgenesis_cli.analytics.scorer import FlowScorer, save_config
from tests.strategies.flow import flow_data, config_data


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


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows_with_gzipped_file(mock_requests_get, tmp_path, mock_amplitude_events):
    """Test extracting flows from Amplitude with gzipped file in the ZIP."""
    # Create a mock ZIP file with gzipped Amplitude data
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        # Create gzipped content
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        gzip_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode="w") as gz_file:
            gz_file.write(event_data.encode("utf-8"))
        
        # Add the gzipped file to the ZIP with a .gz extension
        zip_file.writestr("events.json.gz", gzip_buffer.getvalue())
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response

    # Run command
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_gzip"

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
        ],
    )

    assert result.exit_code == 0
    assert output_dir.exists()
    
    # Check that we processed the events correctly
    flow_files = list(output_dir.glob("*.json"))
    assert len(flow_files) == 1
    
    flow_data = json.loads(flow_files[0].read_text())
    assert flow_data["name"] == "user_flow_session1"
    assert len(flow_data["actions"]) == 2


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows_with_gzip_content_no_extension(mock_requests_get, tmp_path, mock_amplitude_events):
    """Test extracting flows from Amplitude with gzipped content but no .gz extension."""
    # Create a mock ZIP file with gzipped Amplitude data but without .gz extension
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        # Create gzipped content
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        gzip_buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=gzip_buffer, mode="w") as gz_file:
            gz_file.write(event_data.encode("utf-8"))
        
        # Add the gzipped file to the ZIP without a .gz extension
        zip_file.writestr("events.json", gzip_buffer.getvalue())
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response

    # Run command
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_gzip_no_ext"

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
        ],
    )

    assert result.exit_code == 0
    assert output_dir.exists()
    
    # Check that we processed the events correctly
    flow_files = list(output_dir.glob("*.json"))
    assert len(flow_files) == 1
    
    flow_data = json.loads(flow_files[0].read_text())
    assert flow_data["name"] == "user_flow_session1"
    assert len(flow_data["actions"]) == 2


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows_with_corrupted_gz(mock_requests_get, tmp_path, mock_amplitude_events):
    """Test handling of corrupted gzip files."""
    # Create a mock ZIP file with corrupted gzipped data
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        # Create valid events for one file
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        zip_file.writestr("events_valid.json", event_data)
        
        # Create corrupted gzip content (just a few bytes of gzip header)
        corrupted_data = b'\x1f\x8b\x08\x00corrupted gzip data'
        zip_file.writestr("events_corrupted.json.gz", corrupted_data)
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response

    # Run command
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_corrupted_gzip"

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
        ],
    )

    # The command should still succeed, with just a warning about the corrupted file
    assert result.exit_code == 0
    assert "Warning: Error" in result.output
    assert output_dir.exists()
    
    # Check that we processed the valid events
    flow_files = list(output_dir.glob("*.json"))
    assert len(flow_files) == 1
    
    flow_data = json.loads(flow_files[0].read_text())
    assert flow_data["name"] == "user_flow_session1"
    assert len(flow_data["actions"]) == 2


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows_with_encoding_errors(mock_requests_get, tmp_path, mock_amplitude_events):
    """Test handling of encoding errors in file content."""
    # Create a mock ZIP file with valid events and invalid UTF-8 content
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        # Create valid events for one file
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        zip_file.writestr("events_valid.json", event_data)
        
        # Create data with invalid UTF-8 encoding (byte sequence that is not valid UTF-8)
        invalid_utf8 = b'{"event_id": 1, "session_id": "session1", "invalid_field": "\xFF\xFE invalid UTF-8"}'
        zip_file.writestr("events_invalid.json", invalid_utf8)
    
    # Create mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response

    # Run command
    runner = CliRunner()
    output_dir = tmp_path / "test_flows_encoding_errors"

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
        ],
    )

    # The command should still succeed, with just a warning about the encoding error
    assert result.exit_code == 0
    assert "Warning" in result.output
    assert output_dir.exists()
    
    # Check that we processed the valid events
    flow_files = list(output_dir.glob("*.json"))
    assert len(flow_files) == 1
    
    flow_data = json.loads(flow_files[0].read_text())
    assert flow_data["name"] == "user_flow_session1"
    assert len(flow_data["actions"]) == 2


@pytest.fixture
def mock_config():
    """Create a mock configuration file."""
    return {
        "weights": {
            "error_weight": 2.0,
            "business_weight": 1.5
        },
        "business_criticality": {
            "default": 2,
            "login": 5,
            "checkout": 4
        }
    }

@pytest.fixture
def config_file(tmp_path, mock_config):
    """Create a temporary config file."""
    config_path = tmp_path / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(mock_config, f)
    return config_path

def test_flow_scorer_default_config(tmp_path):
    """Test FlowScorer with default configuration."""
    # Create a temporary config file with default values
    config_file = tmp_path / "config.yaml"
    config = {
        "weights": {"error_weight": 2.0, "business_weight": 1.5},
        "business_criticality": {"default": 2}
    }
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    scorer = FlowScorer(str(config_file))
    assert scorer.weights == {"error_weight": 2.0, "business_weight": 1.5}
    assert scorer.business_criticality == {"default": 2}

def test_flow_scorer_load_config(config_file):
    """Test FlowScorer loading configuration from file."""
    scorer = FlowScorer(str(config_file))
    assert scorer.weights["error_weight"] == 2.0
    assert scorer.weights["business_weight"] == 1.5
    assert scorer.business_criticality["login"] == 5
    assert scorer.business_criticality["checkout"] == 4

def test_flow_scorer_get_business_criticality(config_file):
    """Test getting business criticality for different pages."""
    scorer = FlowScorer(str(config_file))
    assert scorer.get_business_criticality("/login") == 5
    assert scorer.get_business_criticality("/checkout") == 4
    assert scorer.get_business_criticality("/unknown") == 2  # default

def test_flow_scorer_calculate_score(tmp_path):
    """Test flow score calculation."""
    # Create a temporary config file
    config_file = tmp_path / "config.yaml"
    config = {
        "weights": {"error_weight": 2.0, "business_weight": 1.5},
        "business_criticality": {
            "default": 2,
            "login": 5,
            "checkout": 4,
            "profile": 3
        }
    }
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    scorer = FlowScorer(str(config_file))
    
    # Test flow with errors and page views
    flow = {
        "frequency": 10,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "data": {"[Amplitude] Page URL": "/login"}
            },
            {"type": "error", "target": "error1"},
            {"type": "error", "target": "error2"}
        ]
    }
    
    result = scorer.calculate_score(flow)
    assert result["frequency"] == 10
    assert result["error_count"] == 2
    assert result["business_criticality"] == 5  # login page criticality
    assert result["score"] == 10 + (2 * 2.0) + (5 * 1.5)  # frequency + (errors * error_weight) + (criticality * business_weight)

def test_config_commands(tmp_path):
    """Test configuration management commands."""
    runner = CliRunner()
    config_file = tmp_path / "config.yaml"
    
    # Test show command with non-existent config
    result = runner.invoke(amplitude, ["config", "show", "--config-path", str(config_file)])
    assert result.exit_code == 0
    assert "Created default configuration at" in result.output
    assert "Please edit the configuration file" in result.output
    
    # Verify the config file was created with default values
    with open(config_file) as f:
        config_data = yaml.safe_load(f)
        assert config_data["weights"]["error_weight"] == 2.0
        assert config_data["weights"]["business_weight"] == 1.5
        assert config_data["business_criticality"]["default"] == 2
        assert config_data["business_criticality"]["login"] == 5
        assert config_data["business_criticality"]["checkout"] == 4
        assert config_data["business_criticality"]["profile"] == 3
    
    # Test set-weight command
    result = runner.invoke(amplitude, [
        "config", "set-weight",
        "--weight-name", "error_weight",
        "--value", "3.0",
        "--config-path", str(config_file)
    ])
    assert result.exit_code == 0
    assert "Updated error_weight to 3.0" in result.output
    
    # Verify the weight was updated
    with open(config_file) as f:
        config_data = yaml.safe_load(f)
        assert config_data["weights"]["error_weight"] == 3.0
    
    # Test set-criticality command
    result = runner.invoke(amplitude, [
        "config", "set-criticality",
        "--page", "profile",
        "--value", "3",
        "--config-path", str(config_file)
    ])
    assert result.exit_code == 0
    assert "Updated criticality for profile to 3" in result.output
    
    # Verify the criticality was updated
    with open(config_file) as f:
        config_data = yaml.safe_load(f)
        assert config_data["business_criticality"]["profile"] == 3

def test_score_flows_command(tmp_path):
    """Test the score-flows CLI command."""
    # Create a test flow file
    flow_file = tmp_path / "user_flow_123.json"
    flow_data = {
        "frequency": 10,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "data": {"[Amplitude] Page URL": "/login"}
            },
            {"type": "error", "target": "error1"}
        ]
    }
    with open(flow_file, 'w') as f:
        json.dump(flow_data, f)
    
    # Test with non-existent config file
    config_file = tmp_path / "config.yaml"
    runner = CliRunner()
    result = runner.invoke(amplitude, [
        "score-flows",
        "--flows-dir", str(tmp_path),
        "--config-path", str(config_file)
    ])
    
    assert result.exit_code == 0
    assert "Created default configuration at" in result.output
    assert "Please edit the configuration file" in result.output
    assert "Flow Scores" in result.output
    assert "user_flow_123.json" in result.output
    assert "10" in result.output  # frequency
    assert "1" in result.output   # error count
    assert "5.0" in result.output # business criticality
    
    # Verify config file was created with values based on flow data
    with open(config_file) as f:
        config = yaml.safe_load(f)
        # With 1 flow and 1 error, error_frequency = 1.0 > 0.5, so error_weight should be 1.5
        assert config["weights"]["error_weight"] == 1.5
        assert config["weights"]["business_weight"] == 1.5
        assert config["business_criticality"]["default"] == 2
        assert config["business_criticality"]["login"] == 5
    
    # Test output to file
    output_file = tmp_path / "scores.json"
    result = runner.invoke(amplitude, [
        "score-flows",
        "--flows-dir", str(tmp_path),
        "--config-path", str(config_file),
        "--output", str(output_file)
    ])
    
    assert result.exit_code == 0
    assert "Saved scores to" in result.output
    with open(output_file) as f:
        scores = json.load(f)
        assert len(scores) == 1
        assert scores[0]["flow_file"] == "user_flow_123.json"
        assert scores[0]["frequency"] == 10
        assert scores[0]["error_count"] == 1
        assert scores[0]["business_criticality"] == 5

# Hypothesis tests
@given(
    flow=flow_data(),
    config=config_data(),
)
@settings(max_examples=10)
def test_flow_scorer_properties(flow, config):
    """Test properties that should always hold for flow scoring."""
    scorer = FlowScorer(config)  # Pass config directly instead of mocking file
    result = scorer.calculate_score(flow)
    
    # Basic properties that should always hold
    assert result["frequency"] == flow["frequency"]
    assert result["error_count"] >= 0
    assert result["score"] >= 0
    
    # Count errors correctly
    expected_errors = sum(1 for action in flow["actions"] 
                        if action["type"].lower().startswith("error"))
    assert result["error_count"] == expected_errors
    
    # Business criticality should be 0 if no page views
    page_views = [action for action in flow["actions"] 
                 if action["type"] == "[Amplitude] Page Viewed"]
    if not page_views:
        assert result["business_criticality"] == 0
        assert result["score"] == flow["frequency"] + (expected_errors * config["weights"]["error_weight"])
    else:
        # Business criticality should be from config or default
        first_page = page_views[0]["data"]["[Amplitude] Page URL"]
        page_name = first_page.split('/')[-1].lower()
        expected_criticality = config["business_criticality"].get(page_name, config["business_criticality"]["default"])
        assert result["business_criticality"] == expected_criticality
        
        # Score should be calculated correctly
        expected_score = (
            flow["frequency"] +
            (expected_errors * config["weights"]["error_weight"]) +
            (expected_criticality * config["weights"]["business_weight"])
        )
        assert result["score"] == expected_score

@given(
    data=st.data(),
)
@settings(max_examples=10)
def test_flow_scorer_edge_cases(data):
    """Test edge cases for flow scoring."""
    config = {
        "weights": {"error_weight": 2.0, "business_weight": 1.5},
        "business_criticality": {"default": 2}
    }
    scorer = FlowScorer(config)  # Pass config directly
    
    # Test empty flow
    empty_flow = {"frequency": 0, "actions": []}
    result = scorer.calculate_score(empty_flow)
    assert result["score"] == 0
    assert result["error_count"] == 0
    assert result["business_criticality"] == 0
    
    # Test flow with only errors
    error_flow = {
        "frequency": 10,
        "actions": [
            {"type": "error", "target": "error1"},
            {"type": "error", "target": "error2"}
        ]
    }
    result = scorer.calculate_score(error_flow)
    assert result["score"] == 10 + (2 * 2.0)  # frequency + (errors * error_weight)
    assert result["business_criticality"] == 0
    
    # Test flow with only page view
    page_flow = {
        "frequency": 10,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "data": {"[Amplitude] Page URL": "/unknown"}
            }
        ]
    }
    result = scorer.calculate_score(page_flow)
    assert result["score"] == 10 + (2 * 1.5)  # frequency + (default criticality * business_weight)
    assert result["error_count"] == 0

@given(
    data=st.data(),
)
@settings(max_examples=5)  # Reduce number of examples
def test_flow_scorer_page_criticality(data):
    """Test business criticality calculation for different pages."""
    config = {
        "weights": {"error_weight": 2.0, "business_weight": 1.5},
        "business_criticality": {
            "default": 2,
            "login": 5,
            "checkout": 4,
            "profile": 3
        }
    }
    scorer = FlowScorer(config)  # Pass config directly
    
    # Test known pages
    pages = ["/login", "/checkout", "/profile", "/unknown"]
    for page in pages:
        flow = {
            "frequency": 10,
            "actions": [
                {
                    "type": "[Amplitude] Page Viewed",
                    "data": {"[Amplitude] Page URL": page}
                }
            ]
        }
        result = scorer.calculate_score(flow)
        page_name = page.split('/')[-1].lower()
        expected_criticality = config["business_criticality"].get(page_name, config["business_criticality"]["default"])
        assert result["business_criticality"] == expected_criticality

def test_flow_scorer_config_generation(tmp_path):
    """Test generating config from flow data."""
    # Create test flow files with different pages and errors
    flows_dir = tmp_path / "test_flows"
    flows_dir.mkdir()
    
    # Flow with login page and errors
    flow1 = {
        "frequency": 10,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "data": {"[Amplitude] Page URL": "/login"}
            },
            {"type": "error", "target": "error1"},
            {"type": "error", "target": "error2"}
        ]
    }
    
    # Flow with checkout page and no errors
    flow2 = {
        "frequency": 5,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "data": {"[Amplitude] Page URL": "/checkout"}
            }
        ]
    }
    
    # Flow with unknown page and errors
    flow3 = {
        "frequency": 3,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "data": {"[Amplitude] Page URL": "/unknown"}
            },
            {"type": "error", "target": "error3"}
        ]
    }
    
    # Write flow files
    with open(flows_dir / "flow1.json", 'w') as f:
        json.dump(flow1, f)
    with open(flows_dir / "flow2.json", 'w') as f:
        json.dump(flow2, f)
    with open(flows_dir / "flow3.json", 'w') as f:
        json.dump(flow3, f)
    
    # Generate config from flows
    config_file = tmp_path / "config.yaml"
    scorer = FlowScorer(str(config_file), str(flows_dir))
    
    # Verify config contents
    with open(config_file) as f:
        config = yaml.safe_load(f)
        
        # Check weights (should be adjusted based on error frequency)
        # With 3 flows and 3 errors, error_frequency = 1.0 > 0.5, so error_weight should be 1.5
        assert config["weights"]["error_weight"] == 1.5
        assert config["weights"]["business_weight"] == 1.5
        
        # Check business criticality
        assert config["business_criticality"]["default"] == 2
        assert config["business_criticality"]["login"] == 5
        assert config["business_criticality"]["checkout"] == 4
        assert "unknown" not in config["business_criticality"]

def test_score_flows_command_with_config_generation(tmp_path):
    """Test the score-flows CLI command with config generation."""
    # Create test flow files
    flows_dir = tmp_path / "test_flows"
    flows_dir.mkdir()
    
    # Create a test flow file with login page and errors
    flow_file = flows_dir / "user_flow_123.json"
    flow_data = {
        "frequency": 10,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "data": {"[Amplitude] Page URL": "/login"}
            },
            {"type": "error", "target": "error1"}
        ]
    }
    with open(flow_file, 'w') as f:
        json.dump(flow_data, f)
    
    # Test with non-existent config file
    config_file = tmp_path / "config.yaml"
    runner = CliRunner()
    result = runner.invoke(amplitude, [
        "score-flows",
        "--flows-dir", str(flows_dir),
        "--config-path", str(config_file)
    ])
    
    assert result.exit_code == 0
    assert "Created default configuration at" in result.output
    assert "Please edit the configuration file" in result.output
    assert "Flow Scores" in result.output
    assert "user_flow_123.json" in result.output
    assert "10" in result.output  # frequency
    assert "1" in result.output   # error count
    assert "5.0" in result.output # business criticality
    
    # Verify config file was created with values based on flow data
    with open(config_file) as f:
        config = yaml.safe_load(f)
        # With 1 flow and 1 error, error_frequency = 1.0 > 0.5, so error_weight should be 1.5
        assert config["weights"]["error_weight"] == 1.5
        assert config["weights"]["business_weight"] == 1.5
        assert config["business_criticality"]["default"] == 2
        assert config["business_criticality"]["login"] == 5
