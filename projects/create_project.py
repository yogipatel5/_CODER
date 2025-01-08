#!/usr/bin/env python3
"""
Project creation automation script that creates new projects based on YAML
configurations. This script handles YAML parsing, project directory creation,
template copying, and environment setup.
"""

import argparse
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
    """
    Parse the YAML configuration file and return its contents as a dictionary.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dictionary containing the parsed YAML configuration

    Raises:
        ConfigurationError: If the file doesn't exist or contains invalid YAML
    """
    try:
        config_path = os.path.expanduser(config_path)
        if not os.path.exists(config_path):
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as config_file:
            try:
                config = yaml.safe_load(config_file)
                if not isinstance(config, dict):
                    raise ConfigurationError("Invalid YAML: Root element must be a mapping")
                logger.info(f"Successfully loaded configuration from {config_path}")
                return config
            except (ParserError, ScannerError) as e:
                raise ConfigurationError(f"Invalid YAML syntax in {config_path}: {str(e)}")

    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        raise


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate the configuration dictionary has all required sections and fields.

    Args:
        config: Dictionary containing the parsed YAML configuration

    Raises:
        ConfigurationError: If required sections or fields are missing
    """
    required_fields = ["project_name", "structure"]

    for field in required_fields:
        if field not in config:
            raise ConfigurationError(f"Missing required field: {field}")

    logger.info("Configuration validation successful")


def create_project_structure(config: Dict[str, Any]) -> str:
    """
    Create the project directory structure based on the configuration.

    Args:
        config: Dictionary containing the parsed YAML configuration

    Returns:
        str: The absolute path to the created project directory

    Raises:
        ConfigurationError: If project creation fails
    """
    try:
        # Get project path and name
        base_path = os.path.expanduser(config.get("path", os.path.expanduser("~/Code/Projects")))
        project_name = config["project_name"]
        project_path = str(os.path.join(base_path, project_name))

        # Create project root directory
        logger.info(f"Creating project directory at: {project_path}")
        os.makedirs(project_path, exist_ok=True)

        # Create directories from structure section
        if "directories" in config["structure"]:
            for directory in config["structure"]["directories"]:
                dir_path = os.path.join(project_path, directory)
                logger.info(f"Creating directory: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)

        # Create empty files from structure section
        if "files" in config["structure"]:
            for file in config["structure"]["files"]:
                file_path = os.path.join(project_path, file)
                # Create parent directories if they don't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # Create empty file if it doesn't exist
                if not os.path.exists(file_path):
                    logger.info(f"Creating file: {file_path}")
                    with open(file_path, "w"):
                        pass  # Create empty file
                else:
                    logger.info(f"File already exists: {file_path}")

        logger.info("Project structure created successfully")
        return project_path

    except OSError as e:
        raise ConfigurationError(f"Failed to create project structure: {str(e)}")


def copy_template_files(config: Dict[str, Any], project_path: str) -> None:
    """
    Copy template files to the project directory based on the configuration.

    Args:
        config: Dictionary containing the parsed YAML configuration
        project_path: Path to the project directory

    Raises:
        ConfigurationError: If template copying fails
    """
    if "templates" not in config:
        logger.info("No templates section found in configuration")
        return

    try:
        # Get the workspace root directory (where the script is run from)
        workspace_root = os.getcwd()

        # Function to copy a single template file
        def copy_single_template(template_path: str) -> None:
            src_path = os.path.join(workspace_root, template_path)
            # Keep the same relative path structure in the destination
            dst_path = os.path.join(project_path, template_path)

            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)

            if not os.path.exists(src_path):
                logger.warning(f"Template file not found: {src_path}")
                return

            if os.path.exists(dst_path):
                logger.info(f"File already exists at destination: {dst_path}")
                return

            import shutil

            logger.info(f"Copying template file: {template_path}")
            shutil.copy2(src_path, dst_path)

        # Function to recursively copy all files from a directory
        def copy_directory_recursive(src_dir: str, base_dir: str) -> None:
            import glob

            # Get all files in the directory and subdirectories
            for src_path in glob.glob(os.path.join(src_dir, "**"), recursive=True):
                if os.path.isfile(src_path):
                    # Get the relative path from the base directory
                    rel_path = os.path.relpath(src_path, base_dir)
                    copy_single_template(rel_path)

        # Copy specified template files
        if config["templates"].get("copy_all", False):
            logger.info("Copying all files from templates directory")
            templates_dir = os.path.join(workspace_root, ".templates")
            if os.path.exists(templates_dir):
                copy_directory_recursive(templates_dir, workspace_root)
            else:
                logger.warning("Templates directory not found: .templates")

        if "files" in config["templates"]:
            for template_file in config["templates"]["files"]:
                copy_single_template(template_file)

        logger.info("Template files copied successfully")

    except (OSError, IOError) as e:
        raise ConfigurationError(f"Failed to copy template files: {str(e)}")


def create_conda_environment(config: Dict[str, Any], project_path: str) -> None:
    """
    Create a conda environment for the project based on the configuration.

    Args:
        config: Dictionary containing the parsed YAML configuration
        project_path: Path to the project directory

    Raises:
        ConfigurationError: If conda environment creation fails
    """
    if "conda" not in config or not config["conda"].get("create_conda_env", False):
        logger.info("Conda environment creation not requested")
        return

    try:
        import subprocess

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
        import json

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


def initialize_git_repository(config: Dict[str, Any], project_path: str) -> None:
    """
    Initialize a git repository and create initial commit.

    Args:
        config: Dictionary containing the parsed YAML configuration
        project_path: Path to the project directory

    Raises:
        ConfigurationError: If git initialization fails
    """
    if "git" not in config or not config["git"].get("create_repo", True):
        logger.info("Git repository creation not requested")
        return

    try:
        import subprocess

        # Change to project directory for git operations
        original_dir = os.getcwd()
        os.chdir(project_path)

        try:
            # Initialize git repository
            logger.info("Initializing git repository")
            subprocess.run(["git", "init"], check=True, capture_output=True)

            # Set initial branch name
            initial_branch = config["git"].get("initial_branch", "main")
            subprocess.run(
                ["git", "checkout", "-b", initial_branch],
                check=True,
                capture_output=True,
            )

            # Add all files
            logger.info("Adding files to git repository")
            subprocess.run(["git", "add", "."], check=True, capture_output=True)

            # Initial commit
            commit_message = config["git"].get("commit_message", "Initial project setup - created by coder")
            logger.info(f"Creating initial commit: {commit_message}")
            subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True)

            # Create additional branches if specified
            if "other_branches" in config["git"]:
                for branch in config["git"]["other_branches"]:
                    logger.info(f"Creating branch: {branch}")
                    subprocess.run(["git", "branch", branch], check=True, capture_output=True)

            logger.info("Git repository initialized successfully")

        finally:
            # Always return to original directory
            os.chdir(original_dir)

    except subprocess.CalledProcessError as e:
        raise ConfigurationError(f"Git command failed: {e.cmd}\nOutput: {e.output.decode()}")
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize git repository: {str(e)}")


def main() -> None:
    """Main entry point for the project creation script."""
    parser = argparse.ArgumentParser(description="Create a new project from YAML configuration")
    parser.add_argument("config", help="Path to the YAML configuration file")
    args = parser.parse_args()

    try:
        config = parse_yaml_config(args.config)
        validate_config(config)
        logger.info("Project configuration loaded successfully")

        # Create project structure
        project_path = create_project_structure(config)
        logger.info(f"Project created at: {project_path}")

        # Copy template files
        copy_template_files(config, project_path)

        # Create conda environment
        create_conda_environment(config, project_path)

        # Initialize git repository
        initialize_git_repository(config, project_path)

        logger.info("Project creation completed successfully")

    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
