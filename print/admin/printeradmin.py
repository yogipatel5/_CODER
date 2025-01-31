from django.contrib import admin
from django.utils.html import format_html

from print.models.printer import Printer


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "location",
        "printer_type",
        "status_badge",
        "default_paper_size",
        "is_default",
        "is_online",
    ]

    list_filter = [
        "printer_type",
        "status",
        "location",
        "color_capable",
        "duplex_capable",
        "airprint_enabled",
        "is_default",
    ]

    search_fields = [
        "name",
        "model",
        "device_name",
        "location",
        "ip_address",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "model",
                    "device_name",
                    "location",
                    "printer_type",
                    "is_default",
                )
            },
        ),
        (
            "Network Settings",
            {
                "fields": (
                    "ip_address",
                    "airprint_enabled",
                )
            },
        ),
        (
            "Status",
            {
                "fields": (
                    "status",
                    "driver_version",
                )
            },
        ),
        (
            "Print Settings",
            {
                "fields": (
                    "default_paper_size",
                    ("custom_paper_width", "custom_paper_height"),
                    "default_media_type",
                    "default_print_quality",
                    "default_color_model",
                )
            },
        ),
        (
            "Capabilities",
            {
                "fields": (
                    "color_capable",
                    "duplex_capable",
                    "supports_custom_paper_size",
                    "resolution_dpi",
                )
            },
        ),
        ("Advanced Options", {"classes": ("collapse",), "fields": ("cups_options",)}),
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
            "ONLINE": "success",
            "OFFLINE": "danger",
            "INK_LOW": "warning",
            "IDLE": "info",
        }
        color = colors.get(obj.status, "secondary")
        return format_html('<span class="badge badge-{}">{}</span>', color, obj.get_status_display())

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"
