from django.db import models
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

from ..managers.task import TaskManager


class Task(models.Model):
    """Model for managing Celery tasks in the print app."""

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
    next_run = models.DateTimeField(null=True, blank=True, help_text="Next scheduled run time")

    # Execution results
    last_status = models.CharField(
        max_length=20,
        choices=[("success", "Success"), ("error", "Error")],
        null=True,
        blank=True,
        help_text="Status of the last execution",
    )
    last_result = models.JSONField(null=True, blank=True, help_text="Results from last successful execution")
    last_error = models.TextField(blank=True, help_text="Error message from last failed execution")

    # Link to Django Celery Beat's PeriodicTask
    periodic_task = models.OneToOneField(
        PeriodicTask,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="print_task",
        help_text="Associated periodic task in Django Celery Beat",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use custom manager
    objects = TaskManager()

    class Meta:
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return f"{self.name} ({self.schedule})"

    def save(self, *args, **kwargs):
        if self.periodic_task:
            self.next_run = self.periodic_task.next_run_at
        super().save(*args, **kwargs)
