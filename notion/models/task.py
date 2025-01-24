# notion/models/task.py
"""Models for managing Celery tasks."""
from django.db import models

from ..managers.task import TaskManager


class Task(models.Model):
    """Model for managing Celery tasks in the Notion app."""

    name = models.CharField(max_length=255, unique=True, help_text="Name of the task")
    description = models.TextField(blank=True, help_text="Description of what this task does")

    # Task settings
    is_active = models.BooleanField(default=True, help_text="Whether this task is enabled")
    notify_on_error = models.BooleanField(default=False, help_text="Whether to send notifications on errors")
    disable_on_error = models.BooleanField(default=False, help_text="Whether to disable task on errors")
    max_retries = models.IntegerField(default=3, help_text="Maximum number of retry attempts")

    # Schedule settings (for periodic tasks)
    schedule = models.CharField(max_length=100, blank=True, help_text="Crontab or interval schedule")
    last_run = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField(null=True, blank=True)

    # Task configuration
    config = models.JSONField(default=dict, help_text="Task-specific configuration options")

    # Error tracking
    error_count = models.IntegerField(default=0, help_text="Number of errors encountered")
    last_error = models.TextField(blank=True, help_text="Last error message")
    last_error_time = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Manager
    objects = TaskManager()

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
