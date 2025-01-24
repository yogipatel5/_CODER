# notion/apps.py
import importlib
import logging
import os
from pathlib import Path

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class NotionConfig(AppConfig):
    """Configuration for the Notion app."""

    name = "notion"
    default_auto_field = "django.db.models.BigAutoField"

    def _import_modules_from_directory(self, directory_name: str) -> None:
        """
        Dynamically import all Python modules from a specified directory.

        Args:
            directory_name (str): Name of the directory to import modules from
        """
        directory = Path(__file__).parent / directory_name
        if not directory.exists():
            return

        for filename in os.listdir(directory):
            if filename.endswith(".py") and not filename.startswith("__"):
                module_name = os.path.splitext(filename)[0]
                try:
                    full_module_path = f"notion.{directory_name}.{module_name}"
                    importlib.import_module(full_module_path)
                except ImportError as e:
                    logger.warning(f"Failed to import {full_module_path}: {str(e)}")

    def ready(self):
        """Initialize the application by importing all required modules."""
        for directory in ["models", "tasks", "admin"]:
            self._import_modules_from_directory(directory)
