from django.db import models
from django.db.models import SET_NULL, OneToOneField

from pfsense.managers.task import TaskManager
from pfsense.models.base_model import BaseModel


class Task(BaseModel):
    """Model for managing Celery tasks in the pfsense app."""

    name = models.CharField(max_length=255, unique=True, help_text="Name of the task")
    description = models.TextField(blank=True, help_text="Description of what this task does")

    # Task settings
    is_active = models.BooleanField(default=True, help_text="Whether this task is active")
    notify_on_error = models.BooleanField(default=False, help_text="Whether to send notifications on errors")
    disable_on_error = models.BooleanField(default=False, help_text="Whether to disable task on errors")
    max_retries = models.IntegerField(default=3, help_text="Maximum number of retry attempts")

    # Schedule settings (for periodic tasks)
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

    objects = TaskManager()

    class Meta:
        app_label = "pfsense"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def next_run(self):
        """Get the next scheduled run time from the periodic task."""
        if self.periodic_task:
            return self.periodic_task.enabled and self.periodic_task.schedule.next()
        return None

    def save(self, *args, **kwargs):
        """Save the task and update its periodic task if needed."""
        # If this is a new task, ensure is_active is set
        if not self.pk and self.is_active is None:
            self.is_active = True

        # Save the task
        super().save(*args, **kwargs)

        # Update periodic task enabled status if it exists
        if self.periodic_task:
            self.periodic_task.enabled = self.is_active
            self.periodic_task.save()

    def disable(self):
        """Disable the task."""
        self.is_active = False
        self.save()
