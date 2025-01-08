"""
Django management command for creating new projects.
"""

import argparse
import logging
import sys
from typing import Any

from django.core.management.base import BaseCommand

from core.services import parse_yaml_config, validate_config

# from projects.github.service import initialize_git_repository
from projects.services import copy_template_files, create_project_structure
from system.services import create_conda_environment

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create a new project from YAML configuration"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("config", help="Path to the YAML configuration file")

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            # Load and validate configuration
            config = parse_yaml_config(options["config"])
            validate_config(config)
            self.stdout.write("Project configuration loaded successfully")

            # Create project structure
            project_path = create_project_structure(config)
            self.stdout.write(f"Project created at: {project_path}")

            # Copy template files
            copy_template_files(config, project_path)

            # Create conda environment
            create_conda_environment(config, project_path)

            # Initialize git repository
            # initialize_git_repository(config, project_path)

            self.stdout.write(
                self.style.SUCCESS("Project creation completed successfully")
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))
            sys.exit(1)
