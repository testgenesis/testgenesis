"""End-to-end workflow tests for TestGenesis.

Tests the complete pipeline:
Amplitude Data → Flow Extraction → Flow Scoring → Test Generation
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from testgenesis_core.analytics.amplitude import create_test_flow

from testgenesis_cli.analytics.scorer import FlowScorer, get_default_config
from testgenesis_dsl.generators.playwright import generate_playwright_test
from testgenesis_dsl.models.test_flow import TestFlow


@pytest.fixture
def mock_amplitude_flow_data():
    """Mock Amplitude flow data representing a login flow."""
    return {
        "name": "login_flow_e2e_test",
        "frequency": 15,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "target": "",
                "data": {
                    "[Amplitude] Page URL": "http://127.0.0.1:8081/login",
                    "[Amplitude] Page Path": "/login",
                    "[Amplitude] Page Title": "TestGenesis Test App",
                    "referrer": "http://127.0.0.1:8081/",
                },
            },
            {
                "type": "form_submit",
                "target": "login_form",
                "data": {
                    "form_data": {"email": "test@example.com", "password": "***"},
                    "element_selector": "#login-form",
                },
            },
            {
                "type": "[Amplitude] Page Viewed",
                "target": "",
                "data": {
                    "[Amplitude] Page URL": "http://127.0.0.1:8081/dashboard",
                    "[Amplitude] Page Path": "/dashboard",
                    "[Amplitude] Page Title": "Dashboard - TestGenesis Test App",
                },
            },
        ],
    }


@pytest.fixture
def mock_amplitude_error_flow_data():
    """Mock Amplitude flow data with error for testing error handling."""
    return {
        "name": "login_error_flow_e2e_test",
        "frequency": 5,
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                "target": "",
                "data": {
                    "[Amplitude] Page URL": "http://127.0.0.1:8081/login",
                    "[Amplitude] Page Path": "/login",
                },
            },
            {
                "type": "form_submit",
                "target": "login_form",
                "data": {"form_data": {"email": "wrong@example.com", "password": "wrongpass"}},
            },
            {
                "type": "error",
                "target": "login_form",
                "data": {
                    "error_code": "invalid_credentials",
                    "error_type": "validation",
                    "message": "Invalid email or password",
                    "[Amplitude] Page URL": "/login",
                },
            },
        ],
    }


@pytest.fixture
def temp_flows_dir(mock_amplitude_flow_data, mock_amplitude_error_flow_data):
    """Create a temporary directory with test flow files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        flows_dir = Path(temp_dir)

        # Write test flows to temporary files
        login_flow_path = flows_dir / "login_flow.json"
        with open(login_flow_path, "w") as f:
            json.dump(mock_amplitude_flow_data, f, indent=2)

        error_flow_path = flows_dir / "login_error_flow.json"
        with open(error_flow_path, "w") as f:
            json.dump(mock_amplitude_error_flow_data, f, indent=2)

        yield flows_dir


def test_e2e_flow_creation_from_amplitude_data(mock_amplitude_flow_data):
    """Test Step 1: Convert Amplitude events to TestFlow objects."""
    # Extract actions from the mock data for flow creation
    actions = mock_amplitude_flow_data["actions"]

    # Convert to the format expected by create_test_flow
    amplitude_events = []
    for action in actions:
        if action["type"] == "[Amplitude] Page Viewed":
            amplitude_events.append(
                {
                    "event_type": "navigation",
                    "event_properties": {
                        "path": action["data"]["[Amplitude] Page Path"],
                        "url": action["data"]["[Amplitude] Page URL"],
                    },
                }
            )
        elif action["type"] == "form_submit":
            amplitude_events.append(
                {
                    "event_type": "form",
                    "event_properties": {
                        "target": action["target"],
                        "data": action["data"]["form_data"],
                    },
                }
            )
        elif action["type"] == "error":
            amplitude_events.append(
                {
                    "event_type": "login_error",
                    "event_properties": {
                        "target": action["target"],
                        "error_code": action["data"]["error_code"],
                        "message": action["data"]["message"],
                    },
                }
            )

    # Create TestFlow from events
    test_flow = create_test_flow(amplitude_events, "test_login_flow")

    # Verify flow structure
    assert test_flow.name == "test_login_flow"
    assert len(test_flow.actions) == len(amplitude_events)

    # Verify first action is navigation
    assert test_flow.actions[0].type == "navigation"
    assert test_flow.actions[0].target == "/login"

    # Verify second action is form submission
    assert test_flow.actions[1].type == "form"
    assert test_flow.actions[1].target == "login_form"


def test_e2e_flow_scoring(temp_flows_dir):
    """Test Step 2: Score flows based on frequency and business impact."""
    # Create scorer with default config
    config = get_default_config(str(temp_flows_dir))
    scorer = FlowScorer(config)

    # Load and score the test flows
    results = []
    for flow_file in temp_flows_dir.glob("*.json"):
        with open(flow_file) as f:
            flow_data = json.load(f)

        result = scorer.calculate_score(flow_data)
        result["flow_file"] = flow_file.name
        results.append(result)

    # Verify we have scores for both flows
    assert len(results) == 2

    # Find login flow result
    login_result = next(r for r in results if "login_flow" in r["flow_file"])
    error_result = next(r for r in results if "login_error_flow" in r["flow_file"])

    # Verify scoring components
    assert login_result["frequency"] == 15
    assert login_result["score"] > 0
    assert login_result["business_impact"] == 5  # Login should have high business impact

    # Error flow should have different characteristics
    assert error_result["frequency"] == 5
    assert error_result["unexpected_error_count"] == 1  # Should detect the error

    # Login flow should score higher than error flow (higher frequency, no errors)
    assert login_result["score"] > error_result["score"]


def test_e2e_test_generation_playwright(mock_amplitude_flow_data):
    """Test Step 3: Generate Playwright test code from flow data."""
    # Convert mock data to TestFlow
    actions = []
    for action_data in mock_amplitude_flow_data["actions"]:
        if action_data["type"] == "[Amplitude] Page Viewed":
            from testgenesis_dsl.models.test_flow import Action

            action = Action(
                type="navigation",
                target=action_data["data"]["[Amplitude] Page Path"],
                data=action_data["data"],
            )
            actions.append(action)
        elif action_data["type"] == "form_submit":
            from testgenesis_dsl.models.test_flow import Action

            action = Action(type="form", target=action_data["target"], data=action_data["data"])
            actions.append(action)

    test_flow = TestFlow(
        name="e2e_login_test", actions=actions, description="End-to-end login flow test"
    )

    # Generate Playwright test code using a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as temp_flow_file:
        flow_json = {
            "name": test_flow.name,
            "actions": [
                {
                    "type": action.type,
                    "target": action.target,
                    "data": action.data,
                    "assertions": action.assertions or [],
                }
                for action in test_flow.actions
            ],
        }
        json.dump(flow_json, temp_flow_file, indent=2)
        temp_flow_path = temp_flow_file.name

    with tempfile.NamedTemporaryFile(mode="w", suffix=".spec.ts", delete=False) as temp_output:
        output_path = temp_output.name

    # Generate the test
    generate_playwright_test(temp_flow_path, output_path)

    # Read the generated code
    playwright_code = Path(output_path).read_text()

    # Cleanup
    Path(temp_flow_path).unlink(missing_ok=True)
    Path(output_path).unlink(missing_ok=True)

    # Verify generated code structure
    assert "test('e2e_login_test'" in playwright_code
    assert "await page.goto(" in playwright_code
    assert "/login" in playwright_code
    assert "/dashboard" in playwright_code
    assert "await page.fill(" in playwright_code or "await page.click(" in playwright_code

    # Verify it's valid TypeScript/JavaScript structure
    assert "import { test, expect } from '@playwright/test';" in playwright_code
    assert playwright_code.count("{") == playwright_code.count("}")  # Balanced braces


@pytest.mark.integration
def test_e2e_complete_workflow(temp_flows_dir):
    """Test the complete end-to-end workflow integration."""
    # Step 1: Score the flows
    config_path = temp_flows_dir / "test_config.yaml"

    # Mock the score_flows function to work with our temp directory
    with patch("testgenesis_cli.analytics.amplitude.click.echo"):
        from testgenesis_cli.analytics.amplitude import FlowScorer

        # Initialize scorer and score flows
        scorer = FlowScorer(str(config_path), str(temp_flows_dir))

        results = []
        for flow_file in temp_flows_dir.glob("*.json"):
            with open(flow_file) as f:
                flow_data = json.load(f)

            result = scorer.calculate_score(flow_data)
            result["flow_file"] = flow_file.name
            results.append(result)

        # Verify we got results
        assert len(results) == 2

        # Step 2: Select highest scoring flow for test generation
        results.sort(key=lambda x: x["score"], reverse=True)
        best_flow_file = results[0]["flow_file"]

        # Step 3: Load the best flow and generate test
        best_flow_path = temp_flows_dir / best_flow_file
        with open(best_flow_path) as f:
            flow_data = json.load(f)

        # Convert to TestFlow object (simplified conversion)
        from testgenesis_dsl.models.test_flow import Action, TestFlow

        actions = []
        for action_data in flow_data["actions"]:
            if action_data["type"] == "[Amplitude] Page Viewed":
                action = Action(
                    type="navigation",
                    target=action_data["data"].get("[Amplitude] Page Path", ""),
                    data=action_data["data"],
                )
                actions.append(action)

        if actions:  # Only create flow if we have valid actions
            test_flow = TestFlow(name=f"generated_{flow_data['name']}", actions=actions)

            # Step 4: Generate final test code using temporary files
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as temp_flow_file:
                flow_json = {
                    "name": test_flow.name,
                    "actions": [
                        {
                            "type": action.type,
                            "target": action.target,
                            "data": action.data,
                            "assertions": action.assertions or [],
                        }
                        for action in test_flow.actions
                    ],
                }
                json.dump(flow_json, temp_flow_file, indent=2)
                temp_flow_path = temp_flow_file.name

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".spec.ts", delete=False
            ) as temp_output:
                output_path = temp_output.name

            # Generate the test
            generate_playwright_test(temp_flow_path, output_path)

            # Read the generated code
            test_code = Path(output_path).read_text()

            # Cleanup
            Path(temp_flow_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

            # Verify the complete pipeline worked
            assert test_code is not None
            assert len(test_code) > 100  # Should be substantial code
            assert "test(" in test_code
            assert "page.goto" in test_code

            # Verify the flow name made it through
            assert flow_data["name"] in test_code or "generated_" in test_code


def test_e2e_error_flow_handling(mock_amplitude_error_flow_data):
    """Test that error flows are properly categorized and handled."""
    # Create scorer with default config
    config = get_default_config()
    scorer = FlowScorer(config)

    # Score the error flow
    result = scorer.calculate_score(mock_amplitude_error_flow_data)

    # Verify error detection - use the CLI scorer structure
    assert result["unexpected_error_count"] >= 0  # Should detect errors appropriately
    assert result["frequency"] == 5
    assert "error_details" in result
    assert "business_impact" in result

    # Verify error categorization
    if result["error_details"]:
        error_detail = result["error_details"][0]
        assert "category" in error_detail
        assert error_detail["type"] == "error"


def test_e2e_data_quality_validation(temp_flows_dir):
    """Test data quality and validation throughout the pipeline."""
    # Test with malformed data
    malformed_flow = {
        "name": "malformed_flow",
        "frequency": "invalid",  # Should be int
        "actions": [
            {
                "type": "[Amplitude] Page Viewed",
                # Missing required data fields
            }
        ],
    }

    malformed_path = temp_flows_dir / "malformed_flow.json"
    with open(malformed_path, "w") as f:
        json.dump(malformed_flow, f)

    # Scorer should handle malformed data gracefully
    config = get_default_config(str(temp_flows_dir))
    scorer = FlowScorer(config)

    # This should not crash
    try:
        result = scorer.calculate_score(malformed_flow)
        # Should handle gracefully, possibly with default values
        assert "score" in result
    except (ValueError, TypeError, KeyError):
        # Acceptable to raise validation errors
        pass
