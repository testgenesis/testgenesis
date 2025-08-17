"""Flow scoring functionality."""

import json
from pathlib import Path
from typing import Any

import yaml


def get_default_config(flows_dir: str | None = None) -> dict[str, Any]:
    """Generate a default configuration based on flow data.
    
    Args:
        flows_dir: Optional directory containing flow files to analyze.
                  If provided, will scan flows to determine pages and weights.
    
    Returns:
        Dict containing the default configuration.
    """
    if not flows_dir:
        return {
            "weights": {
                "error_weight": 2.0,
                "business_weight": 1.5
            },
            "business_impact": {
                "default": 2,
                "login": 5,
                "checkout": 4,
                "profile": 3
            },
            "error_categories": {
                "expected_errors": {
                    "login_error": {
                        "weight": 0.5,
                        "description": "Invalid credentials or user not found",
                        "conditions": [
                            {
                                "property": "error_code",
                                "value": "invalid_credentials",
                                "description": "User provided incorrect credentials"
                            },
                            {
                                "property": "error_code",
                                "value": "user_not_found",
                                "description": "User account does not exist"
                            }
                        ]
                    },
                    "validation_error": {
                        "weight": 0.5,
                        "description": "Form validation errors",
                        "conditions": [
                            {
                                "property": "error_type",
                                "value": "validation",
                                "description": "Form field validation failed"
                            }
                        ]
                    }
                },
                "unexpected_errors": {
                    "login_error": {
                        "weight": 2.0,
                        "description": "Authentication system errors",
                        "conditions": [
                            {
                                "property": "error_code",
                                "value": "auth_service_error",
                                "description": "Authentication service unavailable"
                            },
                            {
                                "property": "error_code",
                                "value": "database_error",
                                "description": "Database connection error during authentication"
                            }
                        ]
                    },
                    "server_error": {
                        "weight": 2.0,
                        "description": "500 server errors",
                        "conditions": [
                            {
                                "property": "status_code",
                                "value": 500,
                                "description": "Internal server error"
                            }
                        ]
                    },
                    "network_error": {
                        "weight": 2.0,
                        "description": "Network connectivity issues",
                        "conditions": [
                            {
                                "property": "error_type",
                                "value": "network",
                                "description": "Network connection failed"
                            }
                        ]
                    }
                }
            }
        }

    # Scan flows to find unique pages and error patterns
    pages = set()
    error_count = 0
    total_flows = 0
    error_types = set()

    for flow_file in Path(flows_dir).glob("*.json"):
        try:
            with open(flow_file) as f:
                flow = json.load(f)
                total_flows += 1

                # Extract pages and error types
                for action in flow.get("actions", []):
                    if action["type"] == "[Amplitude] Page Viewed":
                        page = action["data"]["[Amplitude] Page URL"]
                        pages.add(page)

                    # Count errors and collect error types
                    if action["type"].lower().startswith("error"):
                        error_count += 1
                        error_types.add(action["type"])
        except Exception:
            continue

    # Calculate weights based on data
    error_weight = 2.0
    business_weight = 1.5

    if total_flows > 0:
        # Adjust error weight based on error frequency
        error_frequency = error_count / total_flows
        if error_frequency > 0.5:
            error_weight = 1.5  # Reduce error weight if errors are common
        elif error_frequency < 0.1:
            error_weight = 2.5  # Increase error weight if errors are rare

    # Generate business impact based on page names
    business_impact = {"default": 2}

    # Common page patterns and their impact
    critical_pages = {
        "login": 5,
        "checkout": 4,
        "profile": 3,
        "payment": 4,
        "signup": 4,
        "settings": 3,
        "dashboard": 3,
        "admin": 5,
        "api": 4,
        "auth": 5
    }

    # Add impact for found pages
    for page in pages:
        page_name = page.split('/')[-1].lower()
        if page_name in critical_pages:
            business_impact[page_name] = critical_pages[page_name]

    # Generate error categories based on found error types
    error_categories = {
        "expected_errors": {},
        "unexpected_errors": {}
    }

    # Categorize found error types
    for error_type in error_types:
        error_type_lower = error_type.lower()
        if any(expected in error_type_lower for expected in ["validation", "invalid", "not_found", "unauthorized"]):
            error_categories["expected_errors"][error_type] = {
                "weight": 0.5,
                "description": f"Expected error: {error_type}"
            }
        else:
            error_categories["unexpected_errors"][error_type] = {
                "weight": 2.0,
                "description": f"Unexpected error: {error_type}"
            }

    return {
        "weights": {
            "error_weight": error_weight,
            "business_weight": business_weight
        },
        "business_impact": business_impact,
        "error_categories": error_categories
    }


class FlowScorer:
    """Scorer for user flows based on frequency, errors, and business impact."""

    def __init__(self, config_path_or_dict: str | dict[str, Any], flows_dir: str | None = None):
        """Initialize the scorer with configuration.
        
        Args:
            config_path_or_dict: Path to YAML config file or dict with config data.
            flows_dir: Optional directory containing flow files to analyze.
                      If provided and config doesn't exist, will generate config from flows.
        """
        if isinstance(config_path_or_dict, str):
            config_path = Path(config_path_or_dict)
            if not config_path.exists():
                # Generate config from flows if directory provided
                config_data = get_default_config(flows_dir)
                # Ensure parent directory exists
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                print(f"Created default configuration at {config_path}")
                print("Please edit the configuration file to customize weights and impact values.")
            else:
                with open(config_path) as f:
                    config_data = yaml.safe_load(f)
        else:
            config_data = config_path_or_dict

        self.config = config_data
        self.weights = config_data["weights"]
        self.business_impact = config_data["business_impact"]

    def get_business_impact(self, page_url: str) -> float:
        """Get business impact score for a page.
        
        Args:
            page_url: URL of the page
            
        Returns:
            Business impact score for the page
        """
        page_name = page_url.split('/')[-1].lower()
        return self.business_impact.get(page_name, self.business_impact["default"])

    def calculate_score(self, flow: dict[str, Any]) -> dict[str, Any]:
        """Calculate score for a flow.
        
        Args:
            flow: Dictionary containing flow data with frequency and actions
            
        Returns:
            Dictionary containing score and component values
        """
        frequency = flow.get("frequency", 0)
        actions = flow.get("actions", [])

        # Count errors by category
        expected_error_count = 0
        unexpected_error_count = 0
        error_details = []

        for action in actions:
            if action["type"].lower().startswith("error"):
                error_type = action["type"]
                error_data = action.get("data", {})
                error_categories = self.config.get("error_categories", {})

                # Extract error details
                error_info = {
                    "type": error_type,
                    "message": error_data.get("message", "No message"),
                    "error_code": error_data.get("error_code", "No code"),
                    "error_type": error_data.get("error_type", "No type"),
                    "page": error_data.get("[Amplitude] Page URL", "Unknown page"),
                    "timestamp": error_data.get("timestamp", "Unknown time")
                }

                # Function to check if error matches conditions
                def matches_conditions(conditions):
                    if not conditions:
                        return True
                    for condition in conditions:
                        property_name = condition["property"]
                        expected_value = condition["value"]
                        actual_value = error_data.get(property_name)

                        # Handle numeric values
                        if isinstance(expected_value, (int, float)) and isinstance(actual_value, str):
                            try:
                                actual_value = float(actual_value)
                            except ValueError:
                                continue

                        if actual_value == expected_value:
                            return True
                    return False

                # Check expected errors first
                for category, error_config in error_categories.get("expected_errors", {}).items():
                    if error_type == category and matches_conditions(error_config.get("conditions", [])):
                        expected_error_count += 1
                        error_details.append({
                            **error_info,
                            "category": "expected",
                            "weight": 0,  # Expected errors don't affect score
                            "description": error_config["description"]
                        })
                        break
                else:
                    # Check unexpected errors
                    for category, error_config in error_categories.get("unexpected_errors", {}).items():
                        if error_type == category and matches_conditions(error_config.get("conditions", [])):
                            unexpected_error_count += 1
                            error_details.append({
                                **error_info,
                                "category": "unexpected",
                                "weight": error_config["weight"],
                                "description": error_config["description"]
                            })
                            break
                    else:
                        # Default to unexpected if not categorized
                        unexpected_error_count += 1
                        error_details.append({
                            **error_info,
                            "category": "unexpected",
                            "weight": 2.0,
                            "description": f"Uncategorized error: {error_type}"
                        })

        # Get business impact from first page view
        business_impact = 0
        for action in actions:
            if action["type"] == "[Amplitude] Page Viewed":
                page_url = action["data"]["[Amplitude] Page URL"]
                business_impact = self.get_business_impact(page_url)
                break

        # Calculate total score with only unexpected errors
        error_score = sum(error["weight"] for error in error_details if error["category"] == "unexpected")
        score = (
            frequency +
            (error_score * self.weights["error_weight"]) +
            (business_impact * self.weights["business_weight"])
        )

        return {
            "score": score,
            "frequency": frequency,
            "expected_error_count": expected_error_count,
            "unexpected_error_count": unexpected_error_count,
            "error_details": error_details,
            "business_impact": business_impact
        }


def save_config(config: dict, config_path: str) -> None:
    """Save configuration to YAML file."""
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
