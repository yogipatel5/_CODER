# adwords/models/__init__.py
"""Models for adwords app."""

from shared.models import SharedTask, SharedTaskError

from .manager_model import ManagerAccount


class Task(SharedTask):
    """Model for managing Celery tasks in the adwords app."""

    class Meta(SharedTask.Meta):
        app_label = "adwords"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskError(SharedTaskError):
    """Model for tracking errors in Celery tasks in the adwords app."""

    class Meta(SharedTaskError.Meta):
        app_label = "adwords"
        verbose_name = "Task Error"
        verbose_name_plural = "Task Errors"


__all__ = [
    "Task",
    "TaskError",
    "ManagerAccount",
]
