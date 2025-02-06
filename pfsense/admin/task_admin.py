from django.contrib import admin

from pfsense.models import Task, TaskError
from shared.admin.shared_task import SharedTaskAdmin, SharedTaskErrorAdmin, SharedTaskErrorInline


class TaskErrorInline(SharedTaskErrorInline):
    """Inline admin for TaskError model."""

    model = TaskError


@admin.register(TaskError)
class TaskErrorAdmin(SharedTaskErrorAdmin):
    """Admin interface for TaskError model."""

    pass


@admin.register(Task)
class TaskAdmin(SharedTaskAdmin):
    """Admin interface for Task model."""

    inlines = [TaskErrorInline]
