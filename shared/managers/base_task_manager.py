"""Base manager for shared task functionality."""

import logging
from typing import Optional

from django.apps import apps
from django.db import models

logger = logging.getLogger(__name__)


class BaseTaskManager(models.Manager):
    """Base manager for shared task functionality."""

    def get_task_model_for_name(self, task_name):
        """Get the Task model for a given task name.

        This function iterates through all installed apps and attempts to retrieve the Task model
        associated with the provided task name. It returns the Task model if found, otherwise None.

        Args:
            task_name (str): The name of the task for which to retrieve the model.

        Returns:
            models.Model | None: The Task model if found, otherwise None.
        """
        # First try to find the task in all installed apps
        for app_config in apps.get_app_configs():
            try:
                task_model = app_config.get_model("Task")
                if task_model.objects.filter(name=task_name).exists():
                    return task_model
            except LookupError:
                continue
        return None

    def get_queryset(self):
        """Get queryset with related periodic task.

        This method overrides the default queryset to prefetch the related `periodic_task`.
        This optimization reduces the number of database queries when accessing the related periodic task.

        Returns:
            QuerySet: A queryset with prefetched related periodic task.
        """
        return super().get_queryset().select_related("periodic_task")

    def get_active_task(self, task_name: str) -> Optional["SharedTask"]:  # noqa
        """Get task configuration from the database.

        Args:
            task_name: Name of the task to get configuration for

        Returns:
            Optional[SharedTask]: Task configuration if found and active, None otherwise
        """
        try:
            task = self.get(name=task_name, is_active=True)
            return task
        except self.model.DoesNotExist:
            logger.warning(f"No active task configuration found for {task_name}")
            return None
