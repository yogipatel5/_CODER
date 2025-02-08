# notion/models/__init__.py
"""Models for notion app."""

from django.db import models

from shared.models import SharedTask, SharedTaskError

from .database import Database
from .page import Page


class Task(SharedTask):
    """Model for managing Celery tasks in the notion app."""

    class Meta(SharedTask.Meta):
        app_label = "notion"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskError(SharedTaskError):
    """Task error model for notion app."""

    task = models.ForeignKey("notion.Task", on_delete=models.CASCADE, related_name="errors")


__all__ = [
    "Task",
    "TaskError",
    "Database",
    "Page",
]
