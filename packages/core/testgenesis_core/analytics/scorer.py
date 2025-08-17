"""Core flow scoring functionality."""

import json
from pathlib import Path
from typing import Any

import yaml


def get_default_config(flows_dir: str | None = None) -> dict[str, Any]:
    """Generate a default configuration based on flow data.

    Args:
        flows_dir: Optional directory containing flow files to analyze.
                  If provided, will scan flows to determine error weight.

    Returns:
        Dict containing the default configuration.
    """
    if not flows_dir:
        return {"weights": {"error_weight": 2.0}}

    # Scan flows to find error patterns
    error_count = 0
    total_flows = 0

    for flow_file in Path(flows_dir).glob("*.json"):
        try:
            with open(flow_file) as f:
                flow = json.load(f)
                total_flows += 1

                # Count errors
                for action in flow.get("actions", []):
                    if action["type"].lower().startswith("error"):
                        error_count += 1
        except Exception:
            continue

    # Calculate weights based on data
    error_weight = 2.0

    if total_flows > 0:
        # Adjust error weight based on error frequency
        error_frequency = error_count / total_flows
        if error_frequency > 0.5:
            error_weight = 1.5  # Reduce error weight if errors are common
        elif error_frequency < 0.1:
            error_weight = 2.5  # Increase error weight if errors are rare

    return {"weights": {"error_weight": error_weight}}


class FlowScorer:
    """Scorer for user flows based on frequency and errors."""

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
                with open(config_path, "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False)
            else:
                with open(config_path) as f:
                    config_data = yaml.safe_load(f)
        else:
            config_data = config_path_or_dict

        self.config = config_data
        self.weights = config_data["weights"]

    def calculate_score(self, flow: dict[str, Any]) -> dict[str, Any]:
        """Calculate score for a flow.

        Args:
            flow: Dictionary containing flow data with frequency and actions

        Returns:
            Dictionary containing score and component values
        """
        frequency = flow.get("frequency", 0)
        actions = flow.get("actions", [])

        # Count errors
        error_count = sum(1 for action in actions if action["type"].lower().startswith("error"))

        # Calculate total score
        score = frequency + (error_count * self.weights["error_weight"])

        return {"score": score, "frequency": frequency, "error_count": error_count}


def save_config(config: dict, config_path: str) -> None:
    """Save configuration to YAML file."""
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
