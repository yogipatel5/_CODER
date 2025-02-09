# twilio/models/__init__.py
"""Models for twilio app."""

from django.db import models

from shared.models import SharedTask, SharedTaskError

from .twilio_accounts_model import TwilioAccount
from .twilio_phone_numbers import TwilioPhoneNumber


class Task(SharedTask):
    """Model for managing Celery tasks in the twilio app."""

    class Meta(SharedTask.Meta):
        app_label = "twilio_app"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name


class TaskError(SharedTaskError):
    """Task error model for twilio app."""

    task = models.ForeignKey("twilio_app.Task", on_delete=models.CASCADE, related_name="errors")


__all__ = [
    "Task",
    "TaskError",
    "TwilioAccount",
    "TwilioPhoneNumber",
]
