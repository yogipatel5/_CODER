"""Manager for task state management functionality."""

import logging

from django.db import models

from .base_task_manager import BaseTaskManager

logger = logging.getLogger(__name__)


class TaskStateManager(BaseTaskManager):
    """Manager for task state management functionality."""

    def disable(self, task):
        """Disable the task."""
        task.is_active = False
        self._save_without_periodic_task_update(task)

    def _save_without_periodic_task_update(self, task, *args, **kwargs):
        """Save the task without updating its periodic task to avoid recursion."""
        models.Model.save(task, *args, **kwargs)

    def save_and_update_periodic_task(self, task, *args, **kwargs):
        """Save the task and update its periodic task if needed."""
        # If this is a new task, ensure is_active is set
        if not task.pk and task.is_active is None:
            task.is_active = True

        # Save the task without updating periodic task
        self._save_without_periodic_task_update(task, *args, **kwargs)

        # Update periodic task enabled status if it exists
        if task.periodic_task and task.periodic_task.enabled != task.is_active:
            task.periodic_task.enabled = task.is_active
            task.periodic_task.save()

    def record_task_start(self, task_name):
        """Record that a task has started."""
        task_model = self.get_task_model_for_name(task_name)
        if not task_model:
            logger.warning(f"No task found with name {task_name}")
            return

        task = task_model.objects.filter(name=task_name, is_active=True).first()
        if not task:
            logger.warning(f"Task {task_name} not found or not active")
            return

        task.last_status = "running"
        task.save(update_fields=["last_status"])

    def record_task_success(self, task_name, result=None):
        """Record that a task has completed successfully."""
        task_model = self.get_task_model_for_name(task_name)
        if not task_model:
            logger.warning(f"No task found with name {task_name}")
            return

        task = task_model.objects.filter(name=task_name, is_active=True).first()
        if not task:
            logger.warning(f"Task {task_name} not found or not active")
            return

        task.last_status = "success"
        task.last_result = str(result) if result else None
        task.save(update_fields=["last_status", "last_result"])

    def record_task_error(self, task_name, error):
        """Record that a task has failed."""
        task_model = self.get_task_model_for_name(task_name)
        if not task_model:
            logger.warning(f"No task found with name {task_name}")
            return

        task = task_model.objects.filter(name=task_name, is_active=True).first()
        if not task:
            logger.warning(f"Task {task_name} not found or not active")
            return

        task.last_status = "error"
        task.last_error = str(error)
        task.save(update_fields=["last_status", "last_error", "is_active"])

        # Create error record
        if hasattr(task, "create_error"):
            task.create_error(error)
