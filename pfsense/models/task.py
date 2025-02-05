from django.db.models import SET_NULL, OneToOneField

from shared.models import SharedTask


class Task(SharedTask):
    """Model for managing Celery tasks in the pfsense app. SharedTask imports SharedManager"""

    # App-specific fields
    periodic_task = OneToOneField(
        "django_celery_beat.PeriodicTask",
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_task",
        help_text="Associated periodic task in Django Celery Beat",
    )

    class Meta(SharedTask.Meta):
        app_label = "pfsense"
        verbose_name = "Task"
        verbose_name_plural = "Tasks"
        ordering = ["name"]

    def __str__(self):
        return self.name
