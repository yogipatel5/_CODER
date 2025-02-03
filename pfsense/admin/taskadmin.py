from django.contrib import admin
from django.utils.html import format_html

from pfsense.models.task import Tasks


@admin.register(Tasks)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "last_run_display", "schedule", "notify_on_error", "disable_on_error")
    list_filter = ("is_active", "notify_on_error", "disable_on_error")
    search_fields = ("name", "description")
    readonly_fields = ("last_run",)
    fieldsets = (
        (None, {"fields": ("name", "description")}),
        ("Task Settings", {"fields": ("is_active", "notify_on_error", "disable_on_error", "max_retries")}),
        ("Schedule", {"fields": ("schedule", "last_run")}),
    )

    def last_run_display(self, obj):
        if not obj.last_run:
            return format_html('<span style="color: #999;">Never</span>')
        return obj.last_run

    last_run_display.short_description = "Last Run"
    last_run_display.admin_order_field = "last_run"
