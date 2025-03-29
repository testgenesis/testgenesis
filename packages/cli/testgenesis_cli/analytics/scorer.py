"""Flow scoring functionality."""

import yaml
from pathlib import Path
from typing import Dict, Union, Any


class FlowScorer:
    """Scorer for user flows based on frequency, errors, and business criticality."""

    def __init__(self, config: Union[str, Dict[str, Any]]):
        """Initialize the scorer with configuration.
        
        Args:
            config: Either a path to a YAML config file or a dictionary containing the config
        """
        if isinstance(config, (str, Path)):
            with open(config, 'r') as f:
                config_data = yaml.safe_load(f)
        else:
            config_data = config
            
        self.weights = config_data.get("weights", {
            "error_weight": 2.0,
            "business_weight": 1.5
        })
        self.business_criticality = config_data.get("business_criticality", {
            "default": 2
        })
        # Store the full config for saving later
        self.config = config_data

    def get_business_criticality(self, page_url: str) -> float:
        """Get business criticality score for a page.
        
        Args:
            page_url: URL of the page
            
        Returns:
            Business criticality score for the page
        """
        page_name = page_url.split('/')[-1].lower()
        return self.business_criticality.get(page_name, self.business_criticality["default"])

    def calculate_score(self, flow: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate score for a flow.
        
        Args:
            flow: Dictionary containing flow data with frequency and actions
            
        Returns:
            Dictionary containing score and component values
        """
        frequency = flow.get("frequency", 0)
        actions = flow.get("actions", [])
        
        # Count errors
        error_count = sum(1 for action in actions 
                         if action["type"].lower().startswith("error"))
        
        # Get business criticality from first page view
        business_criticality = 0
        for action in actions:
            if action["type"] == "[Amplitude] Page Viewed":
                page_url = action["data"]["[Amplitude] Page URL"]
                business_criticality = self.get_business_criticality(page_url)
                break
        
        # Calculate total score
        score = (
            frequency +
            (error_count * self.weights["error_weight"]) +
            (business_criticality * self.weights["business_weight"])
        )
        
        return {
            "score": score,
            "frequency": frequency,
            "error_count": error_count,
            "business_criticality": business_criticality
        }


def save_config(config: dict, config_path: str) -> None:
    """Save configuration to YAML file."""
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False) 