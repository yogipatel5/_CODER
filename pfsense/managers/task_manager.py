import logging
from typing import Any, Optional

from celery import Task
from django.db import models
from django.utils import timezone

from notifier.tasks.notify_me import PRIORTY_HIGH, notify_me

logger = logging.getLogger(__name__)


class TaskManager(models.Manager):
    """Manager for handling task execution and error handling."""

    def get_active_task(self, task_name: str) -> Optional["Tasks"]:
        """Get task configuration from the database."""
        try:
            task = self.get(name=task_name, is_active=True)
            logger.info(f"Found active task configuration for {task_name}")
            return task
        except self.model.DoesNotExist:
            logger.warning(f"No active task configuration found for {task_name}")
            return None

    def create_task_wrapper(self, task_name: str):
        """Create a wrapper for Celery tasks that includes error handling."""
        logger.info(f"Creating task wrapper for {task_name}")

        def wrapper(task_func: Task):
            def wrapped_func(*args: Any, **kwargs: Any):
                task_config = self.get_active_task(task_name)

                if not task_config:
                    logger.warning(f"Task {task_name} is not active or not configured, skipping execution")
                    return None

                try:
                    logger.info(f"Executing task {task_name}")
                    result = task_func(*args, **kwargs)
                    logger.info(f"Task {task_name} completed successfully with result: {result}")

                    # Update last run time
                    task_config.last_run = timezone.now()
                    task_config.save()

                    return result

                except Exception as e:
                    error_message = f"Error in task {task_name}: {str(e)}"
                    logger.error(error_message, exc_info=True)

                    # Send notification if configured
                    if task_config.notify_on_error:
                        logger.info(f"Sending error notification for task {task_name}")
                        notify_me(message=error_message, title=f"Task Error: {task_name}", priority=PRIORTY_HIGH)

                    # Disable task if configured
                    if task_config.disable_on_error:
                        logger.info(f"Disabling task {task_name} due to error")
                        task_config.is_active = False
                        task_config.save()

                    # Re-raise the exception for Celery's retry mechanism
                    raise

            return wrapped_func

        return wrapper
