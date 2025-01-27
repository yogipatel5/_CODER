from pathlib import Path

from django.apps import AppConfig


class MeetingsConfig(AppConfig):
    """Django app configuration for your_app_name."""

    name = "personal.meetings"
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
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to import {module_name}: {str(e)}")

    def ready(self):
        """
        Initialize app and register components.
        Auto-discovers and imports modules from specific directories.
        """
        # Auto-discover modules from these directories
        directories_to_import = ["admin", "models", "tasks"]
        for directory in directories_to_import:
            self._import_modules_from_directory(directory)
