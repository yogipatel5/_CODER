# pfsense/models/__init__.py
"""Models for pfsense app."""

from django.db import models

from shared.models import SharedTask, SharedTaskError

from .dhcproute import DHCPRoute


class Task(SharedTask):
    """Model for managing Celery tasks in the pfsense app."""

    class Meta(SharedTask.Meta):
        app_label = "pfsense"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskError(SharedTaskError):
    """Task error model for pfsense app."""

    task = models.ForeignKey("pfsense.Task", on_delete=models.CASCADE, related_name="errors")


__all__ = [
    "Task",
    "TaskError",
    "DHCPRoute",
]
