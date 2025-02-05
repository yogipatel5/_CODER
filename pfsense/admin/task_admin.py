# projects/djhelper/app_folder_template/admin/task_admin.py.template
"""Admin interface for managing Celery tasks."""
from django.contrib import admin

from pfsense.models.task import Task
from pfsense.models.task_error import TaskError
from shared.admin.shared_task import SharedTaskAdmin


class TaskErrorInline(admin.TabularInline):
    """Inline admin for TaskError model."""

    model = TaskError
    extra = 0
    readonly_fields = (
        "error_type",
        "error_message",
        "file_path",
        "function_name",
        "line_number",
        "occurrence_count",
        "first_seen",
        "last_seen",
        "cleared",
        "cleared_at",
        "cleared_by",
    )
    can_delete = False
    max_num = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(TaskError)
class TaskErrorAdmin(admin.ModelAdmin):
    """Admin interface for TaskError model."""

    list_display = (
        "task",
        "error_type",
        "function_name",
        "occurrence_count",
        "last_seen",
        "cleared",
    )
    list_filter = ("cleared", "error_type", "task")
    search_fields = ("error_message", "function_name", "file_path")
    readonly_fields = (
        "task",
        "error_type",
        "error_message",
        "file_path",
        "function_name",
        "line_number",
        "occurrence_count",
        "first_seen",
        "last_seen",
        "cleared",
        "cleared_at",
        "cleared_by",
    )
    actions = ["clear_errors"]
    list_display_links = ("error_type",)
    save_on_top = True

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("task")

    def clear_errors(self, request, queryset):
        for error in queryset:
            error.clear(request.user)
        self.message_user(request, f"Cleared {queryset.count()} errors.")

    clear_errors.short_description = "Clear selected errors"


@admin.register(Task)
class TaskAdmin(SharedTaskAdmin):
    """Admin interface for Task model."""

    inlines = [TaskErrorInline]

    def get_queryset(self, request):
        """Optimize queryset by prefetching related fields."""
        return super().get_queryset(request).prefetch_related("errors")
