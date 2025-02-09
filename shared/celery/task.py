"""Celery task decorator with lifecycle management."""

import logging
from typing import Any, Callable, Dict, Optional

from celery import shared_task as celery_shared_task
from django.apps import apps
from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone
from django_celery_beat.models import (
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
    PeriodicTasks,
    SolarSchedule,
)

from shared.managers.shared_task import SharedTaskManager

logger = logging.getLogger(__name__)


def setup_task_schedule(task_info: Dict[str, Any]) -> None:
    """Set up periodic task schedule in Django Celery Beat.

    Args:
        task_info: Dictionary containing task registration info
    """
    try:
        # Get the schedule configuration
        schedule = task_info["schedule"]
        schedule_type = schedule.get("type", "interval")

        # Create the schedule
        db_schedule = None
        schedule_defaults = {}

        if schedule_type == "interval":
            every = schedule.get("every", 1)
            period = schedule.get("period", "minutes")
            schedule_defaults = {"every": every, "period": period}
            db_schedule, _ = IntervalSchedule.objects.get_or_create(**schedule_defaults)

        elif schedule_type == "crontab":
            cron_defaults = {
                "minute": schedule.get("minute", "*"),
                "hour": schedule.get("hour", "*"),
                "day_of_week": schedule.get("day_of_week", "*"),
                "day_of_month": schedule.get("day_of_month", "*"),
                "month_of_year": schedule.get("month_of_year", "*"),
            }
            db_schedule, _ = CrontabSchedule.objects.get_or_create(**cron_defaults)

        elif schedule_type == "solar":
            solar_defaults = {
                "event": schedule["event"],
                "latitude": schedule["latitude"],
                "longitude": schedule["longitude"],
            }
            db_schedule, _ = SolarSchedule.objects.get_or_create(**solar_defaults)

        # Create/update the periodic task
        defaults = {
            "task": task_info["full_task_name"],
            "name": task_info["full_task_name"],
            "enabled": True,
            "start_time": timezone.now(),  # Set start time to now when creating/updating
        }

        if schedule_type == "interval":
            defaults["interval"] = db_schedule
        elif schedule_type == "crontab":
            defaults["crontab"] = db_schedule
        elif schedule_type == "solar":
            defaults["solar"] = db_schedule

        periodic_task, created = PeriodicTask.objects.update_or_create(
            name=task_info["full_task_name"], defaults=defaults
        )

        # Update PeriodicTasks to ensure the scheduler picks up changes
        PeriodicTasks.update_changed()

        # Get the app's Task model
        app_name = task_info["app_name"]
        Task = apps.get_model(app_name, "Task")

        # Create/update the app's task
        task_defaults = {
            "description": task_info["description"],
            "notify_on_error": task_info["notify_on_error"],
            "disable_on_error": task_info["disable_on_error"],
            "max_retries": task_info["max_retries"],
            "schedule": (
                f"Every {schedule['every']} {schedule['period']}" if schedule_type == "interval" else str(db_schedule)
            ),
            "is_active": True,
        }

        task, created = Task.objects.get_or_create(name=task_info["task_name"], defaults=task_defaults)

        # Link the periodic task
        task.periodic_task = periodic_task
        task.save()

    except Exception as e:
        logger.error(f"Error setting up task schedule: {str(e)}")


# Store task registrations for initialization after Django is ready
_TASK_REGISTRATIONS = {}  # Change to dict to track by app
_INITIALIZED_APPS = set()  # Track which apps have been initialized


@receiver(post_migrate)
def initialize_periodic_tasks(sender, **kwargs):
    """Initialize periodic tasks after Django migrations are complete."""
    try:
        app_label = sender.label if hasattr(sender, "label") else None
        if not app_label or app_label in _INITIALIZED_APPS:
            return

        logger.info(f"Checking periodic tasks for app: {app_label}")

        # Only process tasks for this app
        app_tasks = _TASK_REGISTRATIONS.get(app_label, [])
        if not app_tasks:
            logger.info(f"No tasks registered for app: {app_label}")
            return

        logger.info(f"Initializing {len(app_tasks)} periodic tasks for {app_label}")
        for task_info in app_tasks:
            logger.info(f"Setting up task schedule for {task_info['full_task_name']}")
            setup_task_schedule(task_info)

        # Mark this app as initialized
        _INITIALIZED_APPS.add(app_label)
        logger.info(f"Finished initializing periodic tasks for {app_label}")
    except Exception as e:
        logger.error(f"Error initializing periodic tasks for {app_label}: {str(e)}")


def shared_task(
    func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    bind: bool = True,
    schedule: Optional[Dict] = None,
    description: Optional[str] = None,
    notify_on_error: bool = True,
    disable_on_error: bool = False,
    max_retries: int = 3,
    **kwargs: Any,
) -> Callable:
    """Enhanced shared_task decorator with routing and lifecycle hooks.

    Args:
        func: The function to decorate
        name: Name of the task
        bind: Whether to bind the task to the first argument
        schedule: Schedule configuration for periodic tasks
        description: Description of the task
        notify_on_error: Whether to notify on error
        disable_on_error: Whether to disable the task on error
        max_retries: Maximum number of retries
        **kwargs: Additional keyword arguments

    Returns:
        Decorated task function
    """

    def decorator(fn: Callable) -> Callable:
        # Get the task name
        task_name = name or fn.__name__
        module_name = fn.__module__.split(".")
        app_name = module_name[0]
        full_task_name = f"{app_name}.tasks.{task_name}"

        # Store task registration info
        task_info = {
            "task_name": task_name,
            "full_task_name": full_task_name,
            "app_name": app_name,
            "description": description or fn.__doc__ or "",
            "notify_on_error": notify_on_error,
            "disable_on_error": disable_on_error,
            "max_retries": max_retries,
        }

        if schedule:
            task_info["schedule"] = schedule

        # Apply SharedTaskManager wrapper
        wrapped_func = SharedTaskManager.create_task_wrapper(task_name)(fn)

        # Get app-specific task options
        app_config = getattr(settings, "CELERY_APP_CONFIGS", {}).get(app_name, {})
        task_options = app_config.get("task_options", {})

        # Merge task options with defaults and user-provided options
        final_options = {
            "bind": bind,
            "ignore_result": False,
            "track_started": True,
            "acks_late": True,
            "retry_backoff": True,
            "max_retries": max_retries,
            **task_options,
            **kwargs,
        }

        # Register with Celery
        final_options["name"] = full_task_name  # Always use full task name
        task = celery_shared_task(**final_options)(wrapped_func)

        # Store task info for later initialization
        if schedule:
            app_tasks = _TASK_REGISTRATIONS.setdefault(app_name, [])
            app_tasks.append(task_info)

        return task

    # Handle both @shared_task and @shared_task() syntax
    if func is None:
        return decorator
    return decorator(func)
