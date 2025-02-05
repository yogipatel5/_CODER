"""Base task error model for reuse across apps."""

from django.db import models
from django.utils import timezone


class BaseTaskError(models.Model):
    """Base model for tracking task errors with Sentry-like functionality."""

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
        self.save()

    @classmethod
    def log_error(cls, task, error, traceback):
        """Log an error, creating a new record or updating an existing one."""
        # Extract error information from traceback
        tb = traceback.tb_next  # Skip the current frame
        frame = tb.tb_frame
        error_type = error.__class__.__name__
        file_path = frame.f_code.co_filename
        function_name = frame.f_code.co_name
        line_number = tb.tb_lineno

        # Try to find an existing error
        error_obj, created = cls.objects.get_or_create(
            task=task,
            error_type=error_type,
            file_path=file_path,
            function_name=function_name,
            line_number=line_number,
            cleared=False,
            defaults={
                "error_message": str(error),
            },
        )

        if not created:
            # Update existing error
            error_obj.occurrence_count += 1
            error_obj.last_seen = timezone.now()
            error_obj.save()

        return error_obj
