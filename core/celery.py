"""Celery configuration for the project."""

import os
from pathlib import Path

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")


def get_task_packages():
    """
    Dynamically discover task packages from all installed apps.
    Returns a list of dotted paths to task packages (e.g., ['notion.tasks', 'other_app.tasks'])
    """
    base_dir = Path(__file__).resolve().parent.parent
    task_packages = []

    for app in settings.INSTALLED_APPS:
        # Skip Django's built-in apps and third-party apps
        if app.startswith("django.") or app == "django_celery_beat":
            continue

        # Convert app config path to app name (e.g., 'notion.apps.NotionConfig' -> 'notion')
        app_name = app.split(".")[0] if ".apps." in app else app

        # Check if the app has a tasks directory
        app_tasks_dir = base_dir / app_name / "tasks"
        if app_tasks_dir.exists() and app_tasks_dir.is_dir():
            task_packages.append(f"{app_name}.tasks")

    return task_packages


# Load task modules from all task packages
app.autodiscover_tasks(lambda: get_task_packages())
