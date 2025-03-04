# projects/djhelper/app_folder_template/admin/task_admin.py.template
"""Admin interface for managing Celery tasks."""
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from print.models.task import Task


def format_timedelta(td):
    """Format timedelta into hours and minutes."""
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
        return "< 1m"


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
        ("Task Settings", {"fields": ("is_active", "notify_on_error", "disable_on_error", "max_retries")}),
        ("Schedule", {"fields": ("schedule", "periodic_task", "last_run", "next_run")}),
        ("Execution Results", {"fields": ("last_status", "last_result", "last_error")}),
    )

    def status_display(self, obj):
        if not obj.last_status:
            return format_html('<span style="color: #999;">Unknown</span>')
        elif obj.last_status == "success":
            return format_html('<span style="color: #28a745;">✓</span>')
        else:
            return format_html('<span style="color: #dc3545;">✗</span>')

    status_display.short_description = "Status"

    def last_run_display(self, obj):
        if not obj.last_run:
            return format_html('<span style="color: #999;">Never</span>')

        time_diff = timezone.now() - obj.last_run
        time_str = format_timedelta(time_diff)

        if obj.last_status == "error":
            return format_html('<span style="color: #dc3545;">{} ago</span>', time_str)
        return format_html("{} ago", time_str)

    last_run_display.short_description = "Last Run"
    last_run_display.admin_order_field = "last_run"

    def next_run_display(self, obj):
        if not obj.next_run:
            return format_html('<span style="color: #999;">Not scheduled</span>')

        time_diff = obj.next_run - timezone.now()
        if time_diff.total_seconds() < 0:
            return format_html('<span style="color: #999;">Past due</span>')

        time_str = format_timedelta(time_diff)
        if obj.last_status == "success":
            return format_html('<span style="color: #28a745;">in {}</span>', time_str)
        return format_html("in {}", time_str)

    next_run_display.short_description = "Next Run"
    next_run_display.admin_order_field = "next_run"
