"""Manager for task lifecycle functionality."""

import logging
from functools import wraps
from typing import Any, Callable

from django.utils import timezone

from .base_task_manager import BaseTaskManager

logger = logging.getLogger(__name__)


class TaskLifecycleManager(BaseTaskManager):
    """Manager for task lifecycle functionality."""

    def handle_task_start(self, task_config) -> None:
        """Handle task startup.

        - Records task start time
        - Initializes task state
        - Validates task is enabled

        Args:
            task_config: The task configuration instance
        """
        task_config.last_run = timezone.now()
        task_config.last_status = None
        task_config.last_result = {"message": "Task started", "status": "running"}
        task_config.save(update_fields=["last_run", "last_status", "last_result"])

    def handle_task_success(self, task_config, result: Any) -> None:
        """Handle successful task completion.

        - Updates task status and result
        - Records completion time
        - Clears any error state

        Args:
            task_config: The task configuration instance
            result: The result returned by the task
        """
        # Format result for storage
        if isinstance(result, dict):
            task_result = result
        elif isinstance(result, str):
            task_result = {"message": result}
        else:
            task_result = {"message": str(result)}

        # Always include status and completion time
        task_result["status"] = "success"
        task_result["completed_at"] = timezone.now().isoformat()

        # Update task state
        task_config.last_status = "success"
        task_config.last_result = task_result
        task_config.last_error = ""  # Clear any previous error
        task_config.last_run = timezone.now()  # Update last_run time
        task_config.save(update_fields=["last_status", "last_result", "last_error", "last_run"])

        # Update error tracking if available
        if hasattr(task_config, "errors"):
            task_config.errors.update_regressed_errors(task_config)

    def handle_task_error(self, task_config, error: Exception, traceback=None) -> None:
        """Handle task error.

        - Records error details
        - Updates task status
        - Handles error notifications
        - Manages task disable on error

        Args:
            task_config: The task configuration instance
            error: The exception that occurred
            traceback: Optional traceback info
        """
        error_message = f"Error in task {task_config.name}: {str(error)}"
        logger.error(error_message, exc_info=True)

        # Update task error status
        task_config.last_status = "error"
        task_config.last_error = error_message

        # Handle task disable if configured
        if task_config.disable_on_error:
            task_config.is_active = False

        task_config.save(update_fields=["last_status", "last_error", "is_active"])

        # Log error details
        if traceback:
            task_config.errors.log_error(task_config, error, traceback)

        # Send notification if configured
        if task_config.notify_on_error:
            from notifier.services.notify_me import PRIORITY_HIGH, NotifyMeTask

            NotifyMeTask.notify_me(
                message=error_message,
                title=f"Task Error: {task_config.name}",
                priority=PRIORITY_HIGH,
            )

    @classmethod
    def create_task_wrapper(cls, task_name: str) -> Callable:
        """Create a wrapper for tasks that includes lifecycle management.

        Args:
            task_name: Name of the task to create wrapper for

        Returns:
            callable: Wrapped task function with lifecycle management
        """
        logger.debug(f"Creating task wrapper for {task_name}")

        def wrapper(task_func: Callable) -> Callable:
            @wraps(task_func)
            def wrapped_func(*args: Any, **kwargs: Any) -> Any:
                # Get the task model for this task
                manager = cls()
                task_model = manager.get_task_model_for_name(task_name)
                if not task_model:
                    logger.warning(f"No task model found for {task_name}")
                    return task_func(*args, **kwargs)

                task = task_model.objects.filter(name=task_name, is_active=True).first()
                if not task:
                    logger.warning(f"Task {task_name} not found or not active")
                    return task_func(*args, **kwargs)

                # Record task start
                task_model.objects.record_task_start(task_name)

                try:
                    result = task_func(*args, **kwargs)
                    task_model.objects.record_task_success(task_name, result)
                    return result
                except Exception as e:
                    task_model.objects.record_task_error(task_name, e)
                    raise  # Re-raise for Celery retry handling

            return wrapped_func

        return wrapper
