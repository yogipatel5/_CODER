from django.db import models


class TaskManager(models.Manager):
    """Manager for Task model."""

    def get_active_tasks(self):
        """Get all active tasks."""
        return self.filter(is_active=True)

    def get_errored_tasks(self):
        """Get tasks that have encountered errors."""
        return self.filter(error_count__gt=0)

    def toggle_active_status(self, instance, active):
        """Toggle the active status of a task."""
        instance.is_active = active
        instance.save()
