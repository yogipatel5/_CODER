import logging
from pathlib import Path

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class PrintConfig(AppConfig):
    name = "print"
    verbose_name = "Print"

    def _import_modules_from_directory(self, directory_name: str):
        """
        Import all modules from a directory.

        Args:
            directory_name (str): Name of the directory to import modules from
        """
        try:
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

        except Exception as e:
            logger.error(f"Error importing modules from {directory_name}: {str(e)}")

    def ready(self):
        """
        Initialize the app. This method is called by Django after the app is loaded.
        """
        # Import all modules from these directories
        directories_to_import = ["admin", "models", "tasks"]
        for directory in directories_to_import:
            self._import_modules_from_directory(directory)
