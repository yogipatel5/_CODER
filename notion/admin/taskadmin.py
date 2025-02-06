from django.contrib import admin

# Import your models here
from notion.models.task import Task
from shared.admin import SharedTaskAdmin


@admin.register(Task)
class TaskAdmin(SharedTaskAdmin):
    """Admin interface for notion tasks."""

    list_display = ["name", "is_active", "last_run", "last_run_display"]
    list_filter = ["is_active", "notify_on_error", "disable_on_error"]
    search_fields = ["name", "description"]
    readonly_fields = ["last_run", "next_run", "last_run_display", "next_run_display"]
