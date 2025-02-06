from django.db import models

from shared.models import SharedTaskError


class TaskError(SharedTaskError):
    """Model for task errors in the notion app."""

    task = models.ForeignKey("notion.Task", on_delete=models.CASCADE, related_name="errors")
