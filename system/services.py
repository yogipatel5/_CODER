"""
System management services for handling conda environments and system-level operations.
"""

import json
import logging
import os
import subprocess
from typing import Any, Dict

from core.services import ConfigurationError

logger = logging.getLogger(__name__)


def create_conda_environment(config: Dict[str, Any], project_path: str) -> None:
    """Create a conda environment for the project based on the configuration."""
    if "conda" not in config or not config["conda"].get("create_conda_env", False):
        logger.info("Conda environment creation not requested")
        return

    try:
        # Get conda configuration
        python_version = config["conda"].get("python_version", "3.11")
        env_name = os.path.basename(project_path)
        env_path = os.path.join(project_path, ".conda")

        # Check if environment already exists
        result = subprocess.run(
            ["conda", "env", "list", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        env_list = json.loads(result.stdout)
        env_exists = any(env_path in env for env in env_list.get("envs", []))

        if env_exists:
            logger.info(f"Conda environment already exists at: {env_path}")
            return

        # Create conda environment
        logger.info(f"Creating conda environment '{env_name}' with Python {python_version}")
        subprocess.run(
            ["conda", "create", "-p", env_path, f"python={python_version}", "--yes"],
            check=True,
        )

        # Install requirements if they exist
        requirements_file = os.path.join(project_path, "requirements.txt")
        if os.path.exists(requirements_file):
            logger.info("Installing requirements from requirements.txt")
            # Use pip from the conda environment
            pip_path = os.path.join(env_path, "bin", "pip")
            subprocess.run([pip_path, "install", "-r", requirements_file], check=True)

        logger.info("Conda environment created successfully")

    except subprocess.CalledProcessError as e:
        raise ConfigurationError(f"Failed to create conda environment: {str(e)}")
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Failed to parse conda environment list: {str(e)}")
    except Exception as e:
        raise ConfigurationError(f"Unexpected error creating conda environment: {str(e)}")
