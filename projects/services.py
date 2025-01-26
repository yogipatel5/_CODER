"""
Project management services for creating project structure and handling templates.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict

from core.services import ConfigurationError

logger = logging.getLogger(__name__)


def create_project_structure(config: Dict[str, Any]) -> str:
    """Create the project directory structure based on the configuration."""
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
                    Path(file_path).touch()
                else:
                    logger.info(f"File already exists: {file_path}")

        logger.info("Project structure created successfully")
        return project_path

    except OSError as e:
        raise ConfigurationError(f"Failed to create project structure: {str(e)}")


def copy_template_files(config: Dict[str, Any], project_path: str) -> None:
    """Copy template files to the project directory based on the configuration."""
    if "templates" not in config:
        logger.info("No templates section found in configuration")
        return

    try:
        # Get the workspace root directory (where the script is run from)
        workspace_root = os.getcwd()

        def copy_single_template(template_path: str) -> None:
            src_path = os.path.join(workspace_root, template_path)
            dst_path = os.path.join(project_path, template_path)

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

        def copy_directory_recursive(src_dir: str, base_dir: str) -> None:
            import glob

            for src_path in glob.glob(os.path.join(src_dir, "**"), recursive=True):
                if os.path.isfile(src_path):
                    rel_path = os.path.relpath(src_path, base_dir)
                    copy_single_template(rel_path)

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
