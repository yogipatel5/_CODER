"""Django app configuration for pfsense app."""

import logging
from pathlib import Path

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class NotionConfig(AppConfig):
    """Django app configuration for Notion integration."""

    name = "notion"
    default_auto_field = "django.db.models.BigAutoField"

    def _import_modules_from_directory(self, directory_name: str):
        """
        Dynamically import all Python modules from a specified directory.

        Args:
            directory_name (str): Name of the directory to import modules from
        """
        app_path = Path(__file__).resolve().parent
        directory_path = app_path / directory_name

        if not directory_path.exists():
            return

        for file_path in directory_path.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            module_name = f"{self.name}.{directory_name}.{file_path.stem}"
            try:
                __import__(module_name)
            except ImportError as e:
                logger.warning(f"Failed to import {module_name}: {str(e)}")

    def ready(self):
        """Initialize the application by importing all required modules and setting up periodic tasks."""
        # Import all admin, models and task modules
        self._import_modules_from_directory("admin")
        self._import_modules_from_directory("models")
        self._import_modules_from_directory("tasks")
        self._import_modules_from_directory("signals")
