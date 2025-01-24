import os
from typing import Dict

import yaml


def get_project_config() -> Dict:
    """Read project configuration from project.yaml."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "project.yaml")

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_project_name() -> str:
    """Get project name from project.yaml."""
    return get_project_config().get("project_name", "")
