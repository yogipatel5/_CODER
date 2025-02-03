# projects/djhelper/app_folder_template/admin/task_admin.py.template
"""Admin interface for managing Celery tasks."""
from django.contrib import admin

from ..models.task import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""

    list_display = (
        "name",
        "description",
        "is_active",
        "schedule",
        "last_run",
        "next_run",
        "last_status",
    )
    list_filter = ("is_active", "notify_on_error", "disable_on_error", "last_status")
    search_fields = ("name", "description")
    readonly_fields = (
        "last_run",
        "next_run",
        "last_status",
        "last_result",
        "last_error",
    )
