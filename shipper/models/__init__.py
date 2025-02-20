# shipper/models/__init__.py
"""Models for shipper app."""

from django.db import models

from shared.models import SharedTask, SharedTaskError

from .address_model import AddressModel
from .easypost_account_model import EasyPostAccountModel


class Task(SharedTask):
    """Model for managing Celery tasks in the shipper app."""

    class Meta(SharedTask.Meta):
        app_label = "shipper"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskError(SharedTaskError):
    """Task error model for shipper app."""

    task = models.ForeignKey("shipper.Task", on_delete=models.CASCADE, related_name="errors")


__all__ = [
    "Task",
    "TaskError",
    "EasyPostAccountModel",
    "AddressModel",
]
