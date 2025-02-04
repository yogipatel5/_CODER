# projects/djhelper/app_folder_template/admin/task_admin.py.template
"""Admin interface for managing Celery tasks."""
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from pfsense.models.task import Task


def format_timedelta(td):
    """Format timedelta into hours and minutes."""
    if not td:
        return "never"

    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours and minutes:
        return f"{hours}hr {minutes}m"
    elif hours:
        return f"{hours}hr"
    elif minutes:
        return f"{minutes}m"
    else:
        return "just now"


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""

    list_display = (
        "name",
        "is_active",
        "status_display",
        "last_run_display",
        "next_run_display",
        "schedule",
        "notify_on_error",
    )
    list_filter = ("is_active", "last_status", "notify_on_error")
    search_fields = ("name", "description")
    readonly_fields = ("last_run", "next_run", "last_status", "last_result", "last_error")
    fieldsets = (
        (None, {"fields": ("name", "description")}),
        (
            "Task Settings",
            {"fields": ("is_active", "notify_on_error", "disable_on_error", "max_retries")},
        ),
        ("Schedule", {"fields": ("schedule", "periodic_task", "last_run", "next_run")}),
        ("Execution Results", {"fields": ("last_status", "last_result", "last_error")}),
    )

    def status_display(self, obj):
        """Format status with color."""
        if not obj.last_status:
            return "—"

        colors = {
            "success": "green",
            "error": "red",
        }
        color = colors.get(obj.last_status, "grey")
        return format_html('<span style="color: {}">{}</span>', color, obj.last_status.title())

    def last_run_display(self, obj):
        """Format last run time."""
        if not obj.last_run:
            return "—"

        td = timezone.now() - obj.last_run
        return f"{format_timedelta(td)} ago"

    def next_run_display(self, obj):
        """Format next run time."""
        if not obj.next_run:
            return "—"

        td = obj.next_run - timezone.now()
        if td.total_seconds() < 0:
            return "overdue"
        return f"in {format_timedelta(td)}"

    status_display.short_description = "Status"
    last_run_display.short_description = "Last Run"
    last_run_display.admin_order_field = "last_run"
    next_run_display.short_description = "Next Run"
    next_run_display.admin_order_field = "next_run"
