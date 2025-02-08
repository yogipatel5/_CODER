"""Task model for pfsense app."""

from shared.models import SharedTask


class Task(SharedTask):
    """Model for managing Celery tasks in the pfsense app."""

    class Meta(SharedTask.Meta):
        app_label = "pfsense"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name
