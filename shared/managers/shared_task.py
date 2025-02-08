"""Manager for SharedTask model with task management functionality."""

import json
import logging
from ast import literal_eval
from typing import Any

from celery import current_app

from .task_lifecycle_manager import TaskLifecycleManager
from .task_schedule_manager import TaskScheduleManager
from .task_state_manager import TaskStateManager

logger = logging.getLogger(__name__)


class SharedTaskManager(TaskLifecycleManager, TaskScheduleManager, TaskStateManager):
    """Manager for SharedTask model with task management functionality.

    This manager combines functionality from:
    - TaskLifecycleManager: Task lifecycle (start, success, error) handling
    - TaskScheduleManager: Task scheduling and next run calculation
    - TaskStateManager: Task state management and recording
    """

    def run_task(self, task_or_name) -> Any:
        """Run a periodic task immediately with its configured parameters.

        Args:
            task_or_name: Either a SharedTask instance or a task name string

        Returns:
            Any: Result of the task execution
        """
        # Handle both task instance and task name
        if isinstance(task_or_name, str):
            # Get task by name
            task_config = self.get_active_task(task_or_name)
            if not task_config:
                raise ValueError(f"No active task configuration found for {task_or_name}")
            task = task_config
        else:
            task = task_or_name

        logger.info("Running Task: %s", task.name)
        if not task.is_active:
            logger.warning("Task %s is not active", task.name)
            return False

        # Get the periodic task configuration
        periodic_task = task.periodic_task
        if not periodic_task:
            raise ValueError(f"No periodic task configuration found for {task.name}")

        logger.info("Task Name: %s", periodic_task.task)

        # Parse task parameters from periodic task
        try:
            args = literal_eval(periodic_task.args) if periodic_task.args else []
        except (ValueError, SyntaxError):
            args = json.loads(periodic_task.args) if periodic_task.args else []

        try:
            kwargs = literal_eval(periodic_task.kwargs) if periodic_task.kwargs else {}
        except (ValueError, SyntaxError):
            kwargs = json.loads(periodic_task.kwargs) if periodic_task.kwargs else {}

        # Get additional task options
        task_options = {
            "queue": periodic_task.queue,
            "headers": literal_eval(periodic_task.headers) if periodic_task.headers else None,
            "expires": periodic_task.expires,
            "priority": periodic_task.priority,
        }
        # Filter out None values
        task_options = {k: v for k, v in task_options.items() if v is not None}

        # Get the task from Celery
        celery_task = current_app.tasks.get(periodic_task.task)
        if not celery_task:
            logger.error("Task %s not found in Celery registry", periodic_task.task)
            return False

        logger.info(
            f"Running periodic task {task.name} ({periodic_task.task}) "
            f"with args={args}, kwargs={kwargs}, options={task_options}"
        )

        try:
            # Execute the task with stored parameters
            result = celery_task.apply_async(args=args, kwargs=kwargs, **task_options)
            # Update task state
            self.handle_task_start(task)
            return result
        except Exception as e:
            logger.error(f"Failed to execute task {task.name}: {str(e)}")
            return False
