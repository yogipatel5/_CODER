"""Shared task decorator with integrated routing and lifecycle hooks."""

import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

from celery import current_app
from celery import shared_task as celery_shared_task
from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django_celery_beat.models import (
    CrontabSchedule,
    IntervalSchedule,
    PeriodicTask,
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
        logger.info(f"Setting up periodic task for {task_info['full_task_name']}")

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
        logger.info(f"{'Created' if created else 'Updated'} periodic task {task_info['full_task_name']}")

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

        logger.info(f"Creating/updating app task {task_info['task_name']}")
        task, created = Task.objects.get_or_create(name=task_info["task_name"], defaults=task_defaults)
        logger.info(f"{'Created' if created else 'Updated'} app task {task_info['task_name']}")

        # Link the periodic task
        task.periodic_task = periodic_task
        task.save()
        logger.info(f"Linked periodic task to app task {task_info['task_name']}")

    except Exception as e:
        logger.error(f"Failed to setup periodic task {task_info['task_name']}: {e}", exc_info=True)


def shared_task(
    *args: Any,
    name: Optional[str] = None,
    bind: bool = True,
    schedule: Optional[Dict] = None,
    description: Optional[str] = None,
    notify_on_error: bool = True,
    disable_on_error: bool = False,
    max_retries: int = 3,
    **kwargs: Any,
) -> Callable:
    """Enhanced shared_task decorator with routing and lifecycle hooks."""

    def decorator(func: Callable) -> Callable:
        # Get task name from function if not provided
        task_name = name or func.__name__
        logger.info(f"Decorating task {task_name}")

        # Get app name from module path
        app_name = func.__module__.split(".")[0]

        # Full task path for celery
        full_task_name = f"{app_name}.tasks.{task_name}"
        logger.info(f"Full task name will be {full_task_name}")

        # Apply SharedTaskManager wrapper
        wrapped_func = SharedTaskManager.create_task_wrapper(task_name)(func)

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

        # Create the Celery task
        logger.info(f"Creating Celery task for {full_task_name}")
        final_options["name"] = full_task_name  # Always use full task name
        celery_task = celery_shared_task(**final_options)(wrapped_func)
        logger.info(f"Created Celery task {full_task_name}")

        # Log currently registered tasks
        registered_tasks = list(current_app.tasks.keys())
        filtered_tasks = [task for task in registered_tasks if not task.startswith(("celery.", "_"))]
        logger.info("After registration, available tasks: %s", filtered_tasks)

        # Set up periodic task if needed
        if schedule:
            logger.info(f"Setting up periodic task for {full_task_name}")
            task_info = {
                "task_name": task_name,
                "full_task_name": full_task_name,
                "app_name": app_name,
                "schedule": schedule,
                "description": description or func.__doc__,
                "notify_on_error": notify_on_error,
                "disable_on_error": disable_on_error,
                "max_retries": max_retries,
            }
            setup_task_schedule(task_info)

        return celery_task

    # Handle both @shared_task and @shared_task() syntax
    if len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    return decorator
