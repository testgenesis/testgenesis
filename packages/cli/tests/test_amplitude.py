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
    return [
        Mock(
            user_id="user123",
            session_id="session1",
            event_type="page_view",
            event_properties={"path": "/login"},
        ),
        Mock(
            user_id="user123",
            session_id="session1",
            event_type="form_submit",
            event_properties={
                "form_selector": "#login-form",
                "form_data": {"username": "testuser", "password": "password123"},
            },
        ),
    ]


def test_create_test_flow(mock_amplitude_events):
    """Test converting Amplitude events to a test flow."""
    flow = create_test_flow(mock_amplitude_events)

    assert flow.name == "user_journey_user123"
    assert len(flow.actions) == 2

    assert flow.actions[0].type == "navigation"
    assert flow.actions[0].target == "/login"

    assert flow.actions[1].type == "form"
    assert flow.actions[1].target == "#login-form"
    assert flow.actions[1].data == {"username": "testuser", "password": "password123"}


@patch("testgenesis_cli.analytics.amplitude.Amplitude")
def test_extract_flows(mock_amplitude_class, tmp_path):
    """Test extracting flows from Amplitude."""
    # Mock Amplitude client
    mock_client = Mock()
    mock_client.export_events.return_value = [
        Mock(
            user_id="user123",
            session_id="session1",
            event_type="page_view",
            event_properties={"path": "/login"},
        ),
        Mock(
            user_id="user123",
            session_id="session1",
            event_type="form_submit",
            event_properties={
                "form_selector": "#login-form",
                "form_data": {"username": "testuser", "password": "password123"},
            },
        ),
    ]
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
    assert flow_data["name"] == "user_journey_user123"
    assert len(flow_data["actions"]) == 2
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
