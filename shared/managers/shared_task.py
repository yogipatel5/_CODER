"""Manager for SharedTask model with task management functionality."""

import logging
from functools import wraps
from typing import Optional

from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)


class SharedTaskManager(models.Manager):
    """Manager for SharedTask model with task management functionality."""

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

    def create_task_wrapper(self, task_name: str):
        """Create a wrapper for tasks that includes error handling.

        Args:
            task_name: Name of the task to create wrapper for

        Returns:
            callable: Wrapped task function with error handling
        """
        logger.debug(f"Creating task wrapper for {task_name}")

        def wrapper(task_func):
            @wraps(task_func)
            def inner(*args, **kwargs):
                @wraps(task_func)
                def wrapped_func(*args, **kwargs):
                    # Get task config without select_for_update to avoid outer join issues
                    task_config = self.filter(name=task_name, is_active=True).first()

                    if not task_config:
                        logger.warning(f"Task {task_name} is not active or not configured, skipping execution")
                        return None

                    try:
                        logger.info(f"Executing task {task_name}")
                        result = task_func(*args, **kwargs)
                        logger.info(f"Task {task_name} completed successfully with result: {result}")

                        # Update task status
                        task_config.last_status = "success"
                        task_config.last_result = (
                            result.get("message", str(result)) if isinstance(result, dict) else str(result)
                        )
                        task_config.last_run = timezone.now()
                        self._save_without_periodic_task_update(task_config)

                        # Update error statuses
                        task_config.errors.update_regressed_errors(task_config)

                        return result.get("count", result) if isinstance(result, dict) else result

                    except Exception as e:
                        error_message = f"Error in task {task_name}: {str(e)}"
                        logger.error(error_message, exc_info=True)

                        # Update task error status
                        task_config.last_status = "error"
                        task_config.last_error = error_message
                        task_config.last_run = timezone.now()

                        # Log error using manager
                        import sys

                        task_config.errors.log_error(task_config, e, sys.exc_info()[2])

                        # Disable task if configured
                        if task_config.disable_on_error:
                            logger.info(f"Disabling task {task_name} due to error")
                            task_config.is_active = False

                        # Send notification if configured
                        if task_config.notify_on_error:
                            from notifier.services.notify_me import PRIORITY_HIGH, NotifyMeTask

                            NotifyMeTask.notify_me(
                                message=error_message,
                                title=f"Task Error: {task_name}",
                                priority=PRIORITY_HIGH,
                            )

                        self._save_without_periodic_task_update(task_config)

                        # Re-raise the exception for retry mechanism
                        raise

                return wrapped_func

            return inner

        return wrapper

    def _log_periodic_task_details(self, task):
        """Log details about the periodic task for debugging."""
        logger.info(f"Periodic Task Data for {task.name}:")
        logger.info(f"  - Last Run: {task.last_run}")
        logger.info(f"  - Enabled: {task.periodic_task.enabled}")
        logger.info(f"  - Schedule: {task.periodic_task.schedule}")
        if hasattr(task.periodic_task, "interval"):
            logger.info(f"  - Interval: {task.periodic_task.interval}")
        if hasattr(task.periodic_task, "crontab"):
            logger.info(f"  - Crontab: {task.periodic_task.crontab}")
        if hasattr(task.periodic_task, "solar"):
            logger.info(f"  - Solar: {task.periodic_task.solar}")

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

        self._log_periodic_task_details(task)

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

    def get_last_run_display(self, task):
        """Get a human-readable string of when the task last ran."""
        # Use the last_run from periodic_task as it's more accurate
        if not task.periodic_task or not task.periodic_task.last_run_at:
            return "never"

        now = timezone.now()
        last_run = task.periodic_task.last_run_at
        if timezone.is_naive(last_run):
            last_run = timezone.make_aware(last_run)

        diff = now - last_run

        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return f"{diff.seconds}s ago"

    def get_next_run_display(self, task):
        """Get a human-readable string of when the task will next run."""
        if not task.periodic_task:
            return "—"

        next_run = self.get_next_run(task)
        if not next_run:
            return "—"

        now = timezone.now()
        logger.info(f"Calculating next run display for {task.name}:")
        logger.info(f"  - Next Run: {next_run}")
        logger.info(f"  - Current Time: {now}")

        # Ensure both times are timezone-aware
        if timezone.is_naive(next_run):
            next_run = timezone.make_aware(next_run)

        diff = next_run - now
        total_seconds = int(diff.total_seconds())

        if total_seconds < 0:
            return "now"  # Task is overdue
        elif diff.days > 0:
            return f"in {diff.days}d"
        elif total_seconds >= 3600:
            return f"in {total_seconds // 3600}h"
        elif total_seconds >= 60:
            return f"in {total_seconds // 60}m"
        else:
            return f"in {total_seconds}s"

    def get_error_count_display(self, task):
        """Get a display string for the number of active errors."""
        count = task.errors.filter(cleared=False).count()
        return str(count) if count > 0 else "—"

    def run_task(self, task):
        """Run a task immediately."""
        logger.info("Running Task: %s", task.name)
        if not task.is_active:
            return False

        task_name = task.periodic_task.task if task.periodic_task else None
        logger.info("  - Task Name: %s", task_name)
        if not task_name:
            return False

        # Get the task from Celery's registry
        from celery import current_app

        task_func = current_app.tasks.get(task_name)
        logger.info("task_func: %s", task_func)
        if not task_func:
            return False

        # Run the task
        logger.info(f"running task with delay")
        task_func.delay()
        return True

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
