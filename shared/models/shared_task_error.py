"""Base task error model for reuse across apps."""

from django.db import models
from django.utils import timezone

from shared.managers import SharedTaskErrorManager
from shared.models.shared_task import SharedTask


class SharedTaskError(models.Model):
    """Base model for tracking task errors with Sentry-like functionality."""

    class Status(models.TextChoices):
        NEW = "new", "New"  # Created on the last run
        ONGOING = "ongoing", "Ongoing"  # Happened again on subsequent runs
        REGRESSED = "regressed", "Regressed"  # Didn't happen on last run but happened before
        CLEARED = "cleared", "Cleared"  # Manually cleared by user

    task = models.ForeignKey(
        SharedTask,
        on_delete=models.CASCADE,
        related_name="errors",
        help_text="Task that generated this error",
    )

    error_message = models.TextField(help_text="Full error message")
    error_type = models.CharField(
        max_length=255,
        help_text="Type of the error (e.g., ValueError, ConnectionError)",
    )
    file_path = models.CharField(
        max_length=255,
        help_text="File where the error occurred",
    )
    function_name = models.CharField(
        max_length=255,
        help_text="Function where the error occurred",
    )
    line_number = models.IntegerField(
        help_text="Line number where the error occurred",
    )
    occurrence_count = models.IntegerField(
        default=1,
        help_text="Number of times this error has occurred",
    )
    first_seen = models.DateTimeField(
        auto_now_add=True,
        help_text="When this error was first seen",
    )
    last_seen = models.DateTimeField(
        auto_now=True,
        help_text="When this error was last seen",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        help_text="Current status of the error",
    )
    cleared = models.BooleanField(
        default=False,
        help_text="Whether this error has been cleared",
    )
    cleared_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this error was cleared",
    )
    cleared_by = models.ForeignKey(
        "auth.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_cleared_task_errors",
        help_text="User who cleared this error",
    )

    objects = SharedTaskErrorManager()

    class Meta:
        abstract = True
        ordering = ["-last_seen"]
        unique_together = ["task", "error_type", "file_path", "function_name", "line_number"]

    def __str__(self):
        return f"{self.error_type} in {self.function_name} ({self.occurrence_count} times)"

    def clear(self, user=None):
        """Clear this error."""
        self.cleared = True
        self.cleared_at = timezone.now()
        self.cleared_by = user
        self.status = self.Status.CLEARED
        self.save()
