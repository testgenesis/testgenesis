"""Tests for core analytics functionality."""

import gzip
import io
import json
import zipfile
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from testgenesis_core.analytics.amplitude import (
    create_test_flow,
    extract_user_flows,
    get_today,
    get_yesterday,
)
from testgenesis_core.analytics.scorer import (
    FlowScorer,
    get_default_config,
    save_config,
)


@pytest.fixture
def mock_amplitude_events():
    """Create mock Amplitude events."""
    event1 = {
        "user_id": "user123",
        "session_id": "session1",
        "event_type": "navigation",
        "event_properties": {"path": "/login"},
        "client_event_time": "2024-03-01T12:00:00.000Z",
    }

    event2 = {
        "user_id": "user123",
        "session_id": "session1",
        "event_type": "form",
        "event_properties": {
            "target": "#login-form",
            "data": {"username": "testuser", "password": "password123"},
        },
        "client_event_time": "2024-03-01T12:01:00.000Z",
    }

    return [event1, event2]


@pytest.fixture
def mock_amplitude_response(mock_amplitude_events):
    """Create a mock Amplitude API response."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        event_data = "\n".join(json.dumps(event) for event in mock_amplitude_events)
        zip_file.writestr("events.json", event_data)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    return mock_response


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


@patch("testgenesis_core.analytics.amplitude.requests.get")
def test_extract_user_flows(mock_requests_get, tmp_path, mock_amplitude_response):
    """Test extracting flows from Amplitude."""
    mock_requests_get.return_value = mock_amplitude_response

    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    output_dir = tmp_path / "test_flows"

    flows = extract_user_flows(
        api_key="test-key",
        secret_key="test-secret",
        start_date=start_date,
        end_date=end_date,
        min_frequency=1,
        output_dir=output_dir,
        region="eu",
    )

    # Verify the API call
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    assert kwargs["params"]["start"] == "20240301T00"
    assert kwargs["params"]["end"] == "20240331T23"
    assert kwargs["auth"] == ("test-key", "test-secret")
    assert args[0] == "https://analytics.eu.amplitude.com/api/2/export"

    # Check generated flows
    assert len(flows) == 1
    flow = flows[0]
    assert flow.name == "user_flow_session1"
    assert len(flow.actions) == 2
    assert flow.actions[0].type == "navigation"
    assert flow.actions[0].target == "/login"
    assert flow.actions[1].type == "form"
    assert flow.actions[1].target == "#login-form"

    # Check output files
    assert output_dir.exists()
    flow_files = list(output_dir.glob("*.json"))
    assert len(flow_files) == 1


@patch("testgenesis_core.analytics.amplitude.requests.get")
def test_extract_user_flows_standard_region(mock_requests_get, tmp_path, mock_amplitude_response):
    """Test extracting flows from Amplitude with standard region."""
    mock_requests_get.return_value = mock_amplitude_response

    start_date = datetime(2024, 3, 1)
    end_date = datetime(2024, 3, 31)
    output_dir = tmp_path / "test_flows_standard"

    flows = extract_user_flows(
        api_key="test-key",
        secret_key="test-secret",
        start_date=start_date,
        end_date=end_date,
        min_frequency=1,
        output_dir=output_dir,
        region="standard",
    )

    # Verify the API call uses the standard endpoint
    mock_requests_get.assert_called_once()
    args, kwargs = mock_requests_get.call_args
    assert args[0] == "https://amplitude.com/api/2/export"

    # Check generated flows
    assert len(flows) == 1
    assert output_dir.exists()


@patch("testgenesis_core.analytics.amplitude.requests.get")
def test_extract_user_flows_api_errors(mock_requests_get, tmp_path):
    """Test handling of API errors."""
    # Test 404 error
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_requests_get.return_value = mock_response

    with pytest.raises(ValueError, match="No data available for the time range requested."):
        extract_user_flows(
            api_key="test-key",
            secret_key="test-secret",
            start_date=datetime(2024, 3, 1),
            end_date=datetime(2024, 3, 31),
            output_dir=tmp_path,
        )

    # Test 403 error
    mock_response.status_code = 403
    with pytest.raises(ValueError, match="Authorization failed"):
        extract_user_flows(
            api_key="test-key",
            secret_key="test-secret",
            start_date=datetime(2024, 3, 1),
            end_date=datetime(2024, 3, 31),
            output_dir=tmp_path,
        )

    # Test 504 error
    mock_response.status_code = 504
    with pytest.raises(ValueError, match="The amount of data is large causing a timeout"):
        extract_user_flows(
            api_key="test-key",
            secret_key="test-secret",
            start_date=datetime(2024, 3, 1),
            end_date=datetime(2024, 3, 31),
            output_dir=tmp_path,
        )


@patch("testgenesis_core.analytics.amplitude.requests.get")
def test_extract_user_flows_with_gzipped_file(mock_requests_get, tmp_path, mock_amplitude_events):
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

    # Extract flows using core functionality
    flows = extract_user_flows(
        api_key="test-key",
        secret_key="test-secret",
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 31),
        min_frequency=1,
        output_dir=tmp_path,
    )

    # Verify the results
    assert len(flows) == 1
    flow = flows[0]
    assert flow.name == "user_flow_session1"
    assert len(flow.actions) == 2

    # Check output files if they were created
    if tmp_path.exists():
        flow_files = list(tmp_path.glob("*.json"))
        assert len(flow_files) == 1
        flow_data = json.loads(flow_files[0].read_text())
        assert flow_data["name"] == "user_flow_session1"
        assert len(flow_data["actions"]) == 2


@patch("testgenesis_core.analytics.amplitude.requests.get")
def test_extract_flows_with_gzip_content_no_extension(
    mock_requests_get, tmp_path, mock_amplitude_events
):
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

    # Extract flows using core functionality
    flows = extract_user_flows(
        api_key="test-key",
        secret_key="test-secret",
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 31),
        min_frequency=1,
        output_dir=tmp_path,
    )

    # Verify the results
    assert len(flows) == 1
    flow = flows[0]
    assert flow.name == "user_flow_session1"
    assert len(flow.actions) == 2

    # Check output files if they were created
    if tmp_path.exists():
        flow_files = list(tmp_path.glob("*.json"))
        assert len(flow_files) == 1
        flow_data = json.loads(flow_files[0].read_text())
        assert flow_data["name"] == "user_flow_session1"
        assert len(flow_data["actions"]) == 2


@patch("testgenesis_core.analytics.amplitude.requests.get")
def test_extract_user_flows_with_corrupted_gz(mock_requests_get, tmp_path):
    """Test handling of corrupted gzipped data."""
    # Create corrupted gzipped content
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("events.json.gz", b"corrupted data")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response

    flows = extract_user_flows(
        api_key="test-key",
        secret_key="test-secret",
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 31),
        output_dir=tmp_path,
    )

    assert len(flows) == 0


@patch("testgenesis_core.analytics.amplitude.requests.get")
def test_extract_user_flows_with_encoding_errors(mock_requests_get, tmp_path):
    """Test handling of encoding errors in event data."""
    # Create data with encoding errors
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        zip_file.writestr("events.json", b"invalid utf-8 data: \xff\xfe")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = zip_buffer.getvalue()
    mock_requests_get.return_value = mock_response

    flows = extract_user_flows(
        api_key="test-key",
        secret_key="test-secret",
        start_date=datetime(2024, 3, 1),
        end_date=datetime(2024, 3, 31),
        output_dir=tmp_path,
    )

    assert len(flows) == 0


def test_flow_scorer_default_config(tmp_path):
    """Test creating a flow scorer with default configuration."""
    scorer = FlowScorer(str(tmp_path / "config.yaml"))
    assert scorer.weights["error_weight"] == 2.0


def test_flow_scorer_load_config(config_file):
    """Test loading configuration from file."""
    scorer = FlowScorer(str(config_file))
    assert scorer.weights["error_weight"] == 2.0


def test_flow_scorer_calculate_score(tmp_path):
    """Test calculating score for a flow."""
    # Create test config
    config = {"weights": {"error_weight": 2.0}}

    config_path = tmp_path / "config.yaml"
    save_config(config, str(config_path))

    # Initialize scorer
    scorer = FlowScorer(str(config_path))

    # Test scoring a flow
    flow = {
        "frequency": 10,
        "actions": [
            {"type": "[Amplitude] Page Viewed", "data": {"[Amplitude] Page URL": "/login"}},
            {"type": "error", "data": {"message": "Invalid credentials"}},
        ],
    }

    result = scorer.calculate_score(flow)
    assert result["score"] == 10 + (1 * 2.0)  # frequency + (errors * error_weight)
    assert result["frequency"] == 10
    assert result["error_count"] == 1


@given(
    flow=st.fixed_dictionaries(
        {
            "frequency": st.integers(min_value=0),
            "actions": st.lists(
                st.fixed_dictionaries(
                    {
                        "type": st.sampled_from(["[Amplitude] Page Viewed", "error", "form"]),
                        "data": st.fixed_dictionaries(
                            {
                                "[Amplitude] Page URL": st.sampled_from(
                                    ["/login", "/checkout", "/profile"]
                                ),
                                "message": st.just("Test error"),
                            }
                        ),
                    }
                ),
                min_size=1,
            ),
        }
    ),
    config=st.fixed_dictionaries(
        {
            "weights": st.fixed_dictionaries(
                {"error_weight": st.floats(min_value=0.1, max_value=5.0)}
            )
        }
    ),
)
@settings(max_examples=10)
def test_flow_scorer_properties(flow, config):
    """Test flow scorer properties using hypothesis."""
    scorer = FlowScorer(config)
    result = scorer.calculate_score(flow)

    # Score should be non-negative
    assert result["score"] >= 0

    # Component values should match input
    assert result["frequency"] == flow["frequency"]
    assert result["error_count"] == sum(1 for a in flow["actions"] if a["type"] == "error")


@given(
    data=st.data(),
)
@settings(max_examples=10)
def test_flow_scorer_edge_cases(data):
    """Test flow scorer with edge cases."""
    # Generate random config
    config = {"weights": {"error_weight": data.draw(st.floats(min_value=0.1, max_value=5.0))}}

    scorer = FlowScorer(config)

    # Test empty flow
    empty_flow = {"frequency": 0, "actions": []}
    result = scorer.calculate_score(empty_flow)
    assert result["score"] == 0
    assert result["error_count"] == 0

    # Test flow with errors
    error_flow = {"frequency": 1, "actions": [{"type": "error", "data": {"message": "Test"}}]}
    result = scorer.calculate_score(error_flow)
    assert result["error_count"] == 1
    assert result["score"] == 1 + (1 * config["weights"]["error_weight"])


def test_flow_scorer_config_generation(tmp_path):
    """Test generating configuration from flows."""
    # Create test flows
    flows_dir = tmp_path / "flows"
    flows_dir.mkdir()

    # Create a flow with login page and error
    flow_data = {
        "actions": [
            {"type": "[Amplitude] Page Viewed", "data": {"[Amplitude] Page URL": "/login"}},
            {"type": "error", "data": {"message": "Invalid credentials"}},
        ]
    }

    with open(flows_dir / "test_flow.json", "w") as f:
        json.dump(flow_data, f)

    # Generate config
    config = get_default_config(str(flows_dir))

    # Verify config has correct structure
    assert "weights" in config
    assert "error_weight" in config["weights"]
    assert config["weights"]["error_weight"] > 0
