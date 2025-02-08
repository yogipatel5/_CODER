"""Base task model for reuse across apps."""

from django.db import models
from django.db.models import SET_NULL, OneToOneField

from shared.managers import SharedTaskManager


class SharedTask(models.Model):
    """Base model for all task models across apps."""

    name = models.CharField(max_length=255, unique=True, help_text="Name of the task")
    description = models.TextField(blank=True, help_text="Description of what this task does")

    # Task settings
    is_active = models.BooleanField(default=True, help_text="Whether this task is active")
    notify_on_error = models.BooleanField(default=False, help_text="Whether to send notifications on errors")
    disable_on_error = models.BooleanField(default=False, help_text="Whether to disable task on errors")
    max_retries = models.IntegerField(default=3, help_text="Maximum number of retry attempts")

    # Schedule settings
    schedule = models.CharField(max_length=100, blank=True, help_text="Human-readable schedule description")
    last_run = models.DateTimeField(null=True, blank=True, help_text="Last time the task was run")
    last_status = models.CharField(
        max_length=20,
        choices=[("success", "Success"), ("error", "Error")],
        null=True,
        blank=True,
        help_text="Status of the last execution",
    )

    # Execution results
    last_result = models.JSONField(null=True, blank=True, help_text="Results from last successful execution")
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

    objects = SharedTaskManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        """Delete the task and its associated periodic task."""
        if self.periodic_task:
            self.periodic_task.delete()
        return super().delete(*args, **kwargs)
