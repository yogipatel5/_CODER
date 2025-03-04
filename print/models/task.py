from django.db import models
from django.db.models import SET_NULL, OneToOneField

from print.managers.task import TaskManager
from print.models.base_model import BaseModel


class Task(BaseModel):
    """Model for managing Celery tasks in the print app."""

    name = models.CharField(max_length=255, unique=True, help_text="Name of the task")
    description = models.TextField(blank=True, help_text="Description of what this task does")

    # Task settings
    notify_on_error = models.BooleanField(default=False, help_text="Whether to send notifications on errors")
    disable_on_error = models.BooleanField(default=False, help_text="Whether to disable task on errors")
    max_retries = models.IntegerField(default=3, help_text="Maximum number of retry attempts")

    # Schedule settings (for periodic tasks)
    schedule = models.CharField(max_length=100, blank=True, help_text="Crontab or interval schedule")
    last_run = models.DateTimeField(null=True, blank=True, help_text="Last time the task was run")
    next_run = models.DateTimeField(null=True, blank=True, help_text="Next scheduled run time")
    last_status = models.CharField(
        max_length=20,
        choices=[("success", "Success"), ("error", "Error")],
        null=True,
        blank=True,
        help_text="Status of the last execution",
    )

    # Execution results
    last_result = models.JSONField(
        null=True, blank=True, help_text="Results from last successful execution (e.g., number of items synced)"
    )
    last_error = models.TextField(blank=True, help_text="Error message from last failed execution")

    # Link to Django Celery Beat's PeriodicTask
    periodic_task = OneToOneField(
        "django_celery_beat.PeriodicTask",
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_task",
        help_text="Associated periodic task in Django Celery Beat",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use custom manager
    objects = TaskManager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    def save(self, *args, **kwargs):
        if self.periodic_task:
            # Update next_run from the periodic task
            if self.periodic_task.enabled:
                self.next_run = self.periodic_task.next_run_at
            else:
                self.next_run = None
        super().save(*args, **kwargs)
