from django.db.models import SET_NULL, OneToOneField

from shared.models import SharedTask


class Task(SharedTask):
    """Model for managing Celery tasks in the notion app."""

    class Meta(SharedTask.Meta):
        app_label = "notion"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name
