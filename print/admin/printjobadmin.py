from django.contrib import admin
from django.utils.html import format_html

from ..models.printjob import PrintJob


@admin.register(PrintJob)
class PrintJobAdmin(admin.ModelAdmin):
    list_display = [
        "file_name",
        "printer",
        "status_badge",
        "created_at",
        "copies",
        "paper_size",
        "color_mode",
    ]

    list_filter = [
        "status",
        "printer",
        "paper_size",
        "color_mode",
        "duplex",
    ]

    search_fields = [
        "file_name",
        "printer__name",
        "error_message",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
        "retry_count",
    ]

    fieldsets = [
        (
            "Job Information",
            {
                "fields": (
                    "printer",
                    "file_name",
                    "file_type",
                    "file_size",
                    "file_url",
                    "file_hash",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "started_at",
                    "completed_at",
                    "error_message",
                    "retry_count",
                )
            },
        ),
        (
            "Print Settings",
            {
                "fields": (
                    "copies",
                    "paper_size",
                    "color_mode",
                    "duplex",
                    "custom_settings",
                )
            },
        ),
        (
            "Timestamps",
            {
                "classes": ("collapse",),
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
    ]

    def status_badge(self, obj):
        """Display status as a colored badge"""
        colors = {
            "PENDING": "warning",
            "PROCESSING": "info",
            "COMPLETED": "success",
            "FAILED": "danger",
            "CANCELLED": "secondary",
        }
        color = colors.get(obj.status, "secondary")
        return format_html('<span class="badge badge-{}">{}</span>', color, obj.get_status_display())

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"
