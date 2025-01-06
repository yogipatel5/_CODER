"""
Core services for project configuration and orchestration.
"""

import logging
import os
import sys
from typing import Any, Dict

import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("project_creation.log"),
    ],
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Custom exception for configuration-related errors."""

    pass


def parse_yaml_config(config_path: str) -> Dict[str, Any]:
    """Parse the YAML configuration file and return its contents as a dictionary."""
    try:
        config_path = os.path.expanduser(config_path)
        if not os.path.exists(config_path):
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as config_file:
            try:
                config = yaml.safe_load(config_file)
                if not isinstance(config, dict):
                    raise ConfigurationError(
                        "Invalid YAML: Root element must be a mapping"
                    )
                logger.info(f"Successfully loaded configuration from {config_path}")
                return config
            except (ParserError, ScannerError) as e:
                raise ConfigurationError(
                    f"Invalid YAML syntax in {config_path}: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise


def validate_config(config: Dict[str, Any]) -> None:
    """Validate the configuration dictionary has all required sections and fields."""
    required_fields = ["project_name", "structure"]

    for field in required_fields:
        if field not in config:
            raise ConfigurationError(f"Missing required field: {field}")

    logger.info("Configuration validation successful")
