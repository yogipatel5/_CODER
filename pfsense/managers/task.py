"""Task manager for handling task execution and error handling."""

import logging
from typing import Any, Optional

from celery import Task as CeleryTask
from django.db import models
from django.utils import timezone

from notifier.services.notify_me import PRIORITY_HIGH, NotifyMeTask

logger = logging.getLogger(__name__)


class TaskManager(models.Manager):
    """Manager for handling task execution and error handling."""

    def get_active_task(self, task_name: str) -> Optional["Task"]:  # noqa
        """Get task configuration from the database.

        Args:
            task_name: Name of the task to get configuration for

        Returns:
            Optional[Task]: Task configuration if found and active, None otherwise
        """
        try:
            task = self.get(name=task_name, is_active=True)
            logger.info(f"Found active task configuration for {task_name}")
            return task
        except self.model.DoesNotExist:
            logger.warning(f"No active task configuration found for {task_name}")
            return None

    def create_task_wrapper(self, task_name: str):
        """Create a wrapper for Celery tasks that includes error handling.

        Args:
            task_name: Name of the task to create wrapper for

        Returns:
            callable: Wrapped task function with error handling
        """
        logger.debug(f"Creating task wrapper for {task_name}")

        def wrapper(task_func: CeleryTask):
            def wrapped_func(*args: Any, **kwargs: Any):
                task_config = self.get_active_task(task_name)

                if not task_config:
                    logger.warning(f"Task {task_name} is not active or not configured, skipping execution")
                    return None

                try:
                    logger.info(f"Executing task {task_name}")
                    result = task_func(*args, **kwargs)
                    logger.info(f"Task {task_name} completed successfully with result: {result}")

                    # Update task status
                    task_config.last_status = "success"
                    task_config.last_result = {"result": result}
                    task_config.last_run = timezone.now()
                    task_config.save()

                    return result

                except Exception as e:
                    error_message = f"Error in task {task_name}: {str(e)}"
                    logger.error(error_message, exc_info=True)

                    # Update task error status
                    task_config.last_status = "error"
                    task_config.last_error = error_message
                    task_config.last_run = timezone.now()

                    # Send notification if configured
                    if task_config.notify_on_error:
                        logger.info(f"Sending error notification for task {task_name}")
                        NotifyMeTask.notify_me(
                            message=error_message, title=f"Task Error: {task_name}", priority=PRIORITY_HIGH
                        )

                    # Disable task if configured
                    if task_config.disable_on_error:
                        logger.info(f"Disabling task {task_name} due to error")
                        task_config.is_active = False

                    task_config.save()

                    # Re-raise the exception for Celery's retry mechanism
                    raise

            return wrapped_func

        return wrapper
