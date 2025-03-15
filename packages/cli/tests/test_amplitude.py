"""Tests for Amplitude analytics integration."""

from datetime import datetime
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from testgenesis_cli.analytics.amplitude import amplitude, create_test_flow


@pytest.fixture
def mock_amplitude_events():
    """Create mock Amplitude events."""
    event1 = Mock()
    event1.user_id = "user123"
    event1.session_id = "session1"
    event1.event_type = "navigation"
    event1.event_properties = {"path": "/login"}

    event2 = Mock()
    event2.user_id = "user123"
    event2.session_id = "session1"
    event2.event_type = "form"
    event2.event_properties = {
        "target": "#login-form",
        "data": {"username": "testuser", "password": "password123"},
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


@patch("testgenesis_cli.analytics.amplitude.Amplitude")
def test_extract_flows(mock_amplitude_class, tmp_path):
    """Test extracting flows from Amplitude."""
    # Mock Amplitude client
    mock_client = Mock()
    event1 = Mock()
    event1.user_id = "user123"
    event1.session_id = "session1"
    event1.event_type = "navigation"
    event1.event_properties = {"path": "/login"}
    event1.timestamp = datetime(2024, 3, 1, 12, 0)

    event2 = Mock()
    event2.user_id = "user123"
    event2.session_id = "session1"
    event2.event_type = "form"
    event2.event_properties = {
        "target": "#login-form",
        "data": {"username": "testuser", "password": "password123"},
    }
    event2.timestamp = datetime(2024, 3, 1, 12, 1)

    mock_client.get_events.return_value = [event1, event2]
    mock_amplitude_class.return_value = mock_client

    # Run command
    runner = CliRunner()
    output_dir = tmp_path / "test_flows"

    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
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
    assert flow_data["frequency"] >= 1


def test_extract_flows_invalid_dates():
    """Test handling of invalid date inputs."""
    runner = CliRunner()
    result = runner.invoke(
        amplitude,
        [
            "extract-flows",
            "--api-key",
            "test-key",
            "--start-date",
            "invalid-date",
            "--end-date",
            "2024-03-31",
        ],
    )

    assert result.exit_code != 0
    assert "Error" in result.output
