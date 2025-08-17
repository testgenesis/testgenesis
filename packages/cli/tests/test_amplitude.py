"""Tests for Amplitude CLI commands."""

import io
import json
import zipfile
from unittest.mock import MagicMock, patch

import pytest
import yaml
from click.testing import CliRunner

from testgenesis_cli.analytics.amplitude import amplitude


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


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows_cli(mock_requests_get, tmp_path, mock_amplitude_events):
    """Test the extract-flows CLI command."""
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

    # Verify CLI execution
    assert result.exit_code == 0
    assert output_dir.exists()

    # Check output files
    flow_files = list(output_dir.glob("*.json"))
    assert len(flow_files) == 1
    flow_data = json.loads(flow_files[0].read_text())
    assert flow_data["name"] == "user_flow_session1"
    assert len(flow_data["actions"]) == 2


@patch("testgenesis_cli.analytics.amplitude.requests.get")
def test_extract_flows_cli_standard_region(mock_requests_get, tmp_path, mock_amplitude_events):
    """Test the extract-flows CLI command with standard region."""
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

    # Verify CLI execution
    assert result.exit_code == 0
    assert output_dir.exists()


def test_extract_flows_cli_invalid_dates():
    """Test the extract-flows CLI command with invalid dates."""
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


@pytest.fixture
def mock_config():
    """Create a mock configuration file."""
    return {
        "weights": {
            "error_weight": 2.0,
            "business_weight": 1.5
        },
        "business_impact": {
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
        assert config_data["business_impact"]["default"] == 2
        assert config_data["business_impact"]["login"] == 5
        assert config_data["business_impact"]["checkout"] == 4
        assert config_data["business_impact"]["profile"] == 3

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

    # Test set-impact command
    result = runner.invoke(amplitude, [
        "config", "set-impact",
        "--page", "profile",
        "--value", "3",
        "--config-path", str(config_file)
    ])
    assert result.exit_code == 0
    assert "Updated impact for profile to 3" in result.output

    # Verify the impact was updated
    with open(config_file) as f:
        config_data = yaml.safe_load(f)
        assert config_data["business_impact"]["profile"] == 3


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
            {
                "type": "error",
                "data": {
                    "error_code": "auth_service_error",
                    "message": "Authentication service unavailable"
                }
            }
        ]
    }
    with open(flow_file, 'w') as f:
        json.dump(flow_data, f)

    # Test with non-existent config file
    config_file = tmp_path / "testgenesis.config"
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
    assert "0" in result.output   # expected_error_count
    assert "1" in result.output   # unexpected_error_count
    assert "5.0" in result.output # business impact

    # Verify config file was created with values based on flow data
    with open(config_file) as f:
        config = yaml.safe_load(f)
        # With 1 flow and 1 unexpected error, error_frequency = 1.0 > 0.5, so error_weight should be 1.5
        assert config["weights"]["error_weight"] == 1.5
        assert config["weights"]["business_weight"] == 1.5
        assert config["business_impact"]["default"] == 2
        assert config["business_impact"]["login"] == 5

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
        assert scores[0]["expected_error_count"] == 0
        assert scores[0]["unexpected_error_count"] == 1
        assert scores[0]["business_impact"] == 5
