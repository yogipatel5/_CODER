"""Manager for SharedTask model with task management functionality."""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

from django.apps import apps
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class SharedTaskManager(models.Manager):
    """Manager for SharedTask model with task management functionality."""

    def get_task_model_for_name(self, task_name):
        """Get the Task model for a given task name."""
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
        """Get queryset with related periodic task."""
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
            logger.info(f"Found active task configuration for {task_name}")
            return task
        except self.model.DoesNotExist:
            logger.warning(f"No active task configuration found for {task_name}")
            return None

    def handle_task_start(self, task_config) -> None:
        """Handle task startup.

        - Records task start time
        - Initializes task state
        - Validates task is enabled

        Args:
            task_config: The task configuration instance
        """
        logger.info(f"Starting task {task_config.name}")
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
        logger.info(f"Task {task_config.name} completed successfully")

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
            logger.info(f"Disabling task {task_config.name} due to error")
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

    @classmethod
    def list_registered_tasks(cls) -> list:
        """Get a list of all registered task names, excluding Celery internal tasks.

        Returns:
            list: List of registered task names
        """
        from celery import current_app

        # Get all registered task names
        registered_tasks = list(current_app.tasks.keys())

        # Filter out built-in Celery tasks and internal tasks
        filtered_tasks = [task for task in registered_tasks if not task.startswith(("celery.", "_"))]

        return sorted(filtered_tasks)

    @classmethod
    def verify_task_registration(cls, task_name: str) -> bool:
        """Verify that a task is properly registered with Celery.

        Args:
            task_name: Full task name to verify (e.g. 'pfsense.tasks.sync_dhcp_routes')

        Returns:
            bool: True if task is registered, False otherwise
        """
        from celery import current_app

        return task_name in current_app.tasks

    def _get_last_run(self, task) -> Optional[timezone.datetime]:
        """Get the timezone-aware last run time from the periodic task."""
        # Use the last_run from periodic_task as it's more accurate
        if not task.periodic_task or not task.periodic_task.last_run_at:
            return None

        last_run = task.periodic_task.last_run_at
        if timezone.is_naive(last_run):
            last_run = timezone.make_aware(last_run)

        logger.info(f"Getting last run time for {task.name}:")
        logger.info(f"  - Periodic Task Last Run: {last_run}")
        logger.info(f"  - Task Model Last Run: {task.last_run}")

        return last_run

    def _calculate_next_run_for_interval(self, task, last_run: timezone.datetime) -> timezone.datetime:
        """Calculate the next run time for an interval schedule."""
        interval = task.periodic_task.interval

        # Convert the interval to timedelta
        if interval.period == "days":
            td = timezone.timedelta(days=interval.every)
        elif interval.period == "hours":
            td = timezone.timedelta(hours=interval.every)
        elif interval.period == "minutes":
            td = timezone.timedelta(minutes=interval.every)
        elif interval.period == "seconds":
            td = timezone.timedelta(seconds=interval.every)
        else:
            # Default to hourly if unknown period
            td = timezone.timedelta(hours=1)

        # Calculate next run time
        next_run = last_run + td
        now = timezone.now()

        # If next run is in the past, calculate the next occurrence from now
        if next_run < now:
            # Calculate how many intervals have passed
            time_since_last = now - last_run
            intervals_passed = (time_since_last.total_seconds() // td.total_seconds()) + 1
            next_run = last_run + (td * int(intervals_passed))

        logger.info(f"Calculated next run for {task.name}:")
        logger.info(f"  - Last Run: {last_run}")
        logger.info(f"  - Interval: {td}")
        logger.info(f"  - Next Run: {next_run}")
        logger.info(f"  - Current Time: {now}")
        return next_run

    def _calculate_next_run_for_crontab(self, task) -> Optional[timezone.datetime]:
        """Calculate the next run time for a crontab schedule."""
        from django_celery_beat.schedulers import crontab_parser

        crontab = task.periodic_task.crontab
        parser = crontab_parser(60)
        next_run = parser.next(timezone.now(), crontab)
        if timezone.is_naive(next_run):
            next_run = timezone.make_aware(next_run)
        return next_run

    def _calculate_next_run_for_solar(self, task) -> Optional[timezone.datetime]:
        """Calculate the next run time for a solar schedule."""
        # Solar schedules are not supported yet
        return None

    def _calculate_next_run_for_schedule(self, task, last_run: timezone.datetime) -> Optional[timezone.datetime]:
        """Calculate the next run time for a generic schedule."""
        schedule = task.periodic_task.schedule
        if not hasattr(schedule, "run_every"):
            return None

        next_run = last_run + timezone.timedelta(seconds=schedule.run_every.total_seconds())
        now = timezone.now()

        # If next run is in the past, calculate the next occurrence from now
        if next_run < now:
            time_since_last = now - last_run
            run_every = timezone.timedelta(seconds=schedule.run_every.total_seconds())
            intervals_passed = (time_since_last.total_seconds() // run_every.total_seconds()) + 1
            next_run = last_run + (run_every * int(intervals_passed))

        return next_run

    def get_next_run(self, task) -> Optional[timezone.datetime]:
        """Get the next scheduled run time from the periodic task.

        Args:
            task: The SharedTask instance.

        Returns:
            Optional[timezone.datetime]: The next run time, or None if the task is not scheduled.
        """
        if not task.periodic_task or not task.periodic_task.enabled:
            return None

        last_run = self._get_last_run(task)
        if last_run is None:
            return timezone.now()

        # Handle different schedule types
        if task.periodic_task.interval:
            return self._calculate_next_run_for_interval(task, last_run)
        elif task.periodic_task.crontab:
            return self._calculate_next_run_for_crontab(task)
        elif task.periodic_task.solar:
            return self._calculate_next_run_for_solar(task)
        elif task.periodic_task.schedule:
            return self._calculate_next_run_for_schedule(task, last_run)

        return None

    def run_task(self, task_or_name) -> Any:
        """Run a periodic task immediately with its configured parameters.

        Args:
            task_or_name: Either a SharedTask instance or a task name string

        Returns:
            Any: Result of the task execution
        """
        import json
        from ast import literal_eval

        from celery import current_app

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
        task.save(update_fields=["last_status", "last_error"])

        # Create error record
        if hasattr(task, "create_error"):
            task.create_error(error)


def task_lifecycle(func):
    """Decorator to manage task lifecycle."""

    @wraps(func)
    def wrapped_func(*args, **kwargs):
        task_name = func.__name__
        task_model = SharedTaskManager().get_task_model_for_name(task_name)
        if not task_model:
            logger.warning(f"No task found with name {task_name}")
            return func(*args, **kwargs)

        task = task_model.objects.filter(name=task_name, is_active=True).first()
        if not task:
            logger.warning(f"Task {task_name} not found or not active")
            return func(*args, **kwargs)

        task.objects.record_task_start(task_name)

        try:
            result = func(*args, **kwargs)
            task.objects.record_task_success(task_name, result)
            return result
        except Exception as e:
            task.objects.record_task_error(task_name, e)
            raise

    return wrapped_func
