import logging
import os
from pathlib import Path

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class NotionConfig(AppConfig):
    """Django app configuration for Notion integration."""

    name = "notion"
    default_auto_field = "django.db.models.BigAutoField"

    # TODO: Move periodic task configuration to a dedicated service
    # TODO: Add health checks for Notion API connection
    # TODO: Implement proper startup validation for required settings
    # TODO: Add signal handlers for model operations

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

    def _setup_periodic_tasks(self):
        """Set up periodic tasks for Notion sync."""
        from django_celery_beat.models import IntervalSchedule, PeriodicTask

        try:
            # Create or get the interval schedule (every 5 minutes)
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=5,
                period=IntervalSchedule.MINUTES,
            )

            # Create or update the periodic task
            PeriodicTask.objects.update_or_create(
                name="sync_notion_content",
                defaults={
                    "task": "notion.tasks.sync.sync_notion_content",
                    "interval": schedule,
                    "enabled": True,
                },
            )
            logger.info("Successfully set up Notion sync periodic task")
        except Exception as e:
            logger.error(f"Error setting up periodic tasks: {e}")

    def ready(self):
        """Initialize the application by importing all required modules and setting up periodic tasks."""
        # Import all admin and task modules
        self._import_modules_from_directory("admin")
        self._import_modules_from_directory("tasks")

        # Set up periodic tasks, but only if we're not in a management command
        import sys

        if "manage.py" not in sys.argv[0]:
            self._setup_periodic_tasks()
