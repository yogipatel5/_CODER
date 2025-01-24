from django.db import models
from django.utils import timezone


class NotionAgentJobManager(models.Manager):
    """Manager for NotionAgentJob model."""

    def mark_completed(self, instance, result=None):
        """Mark the task as completed with optional results."""
        instance.status = instance.Status.COMPLETED
        if result:
            instance.result = result
        instance.completed_at = timezone.now()
        instance.save()

    def mark_failed(self, instance, error_message):
        """Mark the task as failed with error message."""
        instance.status = instance.Status.FAILED
        instance.error_message = error_message
        instance.completed_at = timezone.now()
        instance.save()
