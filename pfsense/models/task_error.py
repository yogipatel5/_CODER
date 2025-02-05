from django.db import models

from shared.models import SharedTaskError


class TaskError(SharedTaskError):
    task = models.ForeignKey("pfsense.Task", on_delete=models.CASCADE, related_name="errors")
