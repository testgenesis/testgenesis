"""Test configuration for testgenesis-core."""

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def test_data_dir():
    """Fixture to provide path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def config_file(tmp_path):
    """Create a test configuration file."""
    config = {
        "weights": {"error_weight": 2.0, "business_weight": 1.5},
        "business_criticality": {"default": 2, "login": 5, "checkout": 4, "profile": 3},
    }

    config_path = tmp_path / "test_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config, f)

    return config_path
