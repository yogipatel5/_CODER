"""Django admin configuration for the Notion app."""

from django.contrib import admin
from django.utils.html import format_html

from notion.models.notionagentjobs import NotionAgentJob


@admin.register(NotionAgentJob)
class NotionAgentJobAdmin(admin.ModelAdmin):
    """Admin interface for NotionAgentJob model."""

    list_display = [
        "page_id",
        "status",
        "created_at",
        "updated_at",
        "view_page_link",
    ]
    list_filter = ["status", "created_at", "updated_at"]
    search_fields = ["page_id", "description", "task_details"]
    readonly_fields = ["created_at", "updated_at", "completed_at"]

    fieldsets = [
        ("Page Information", {"fields": ["page_id", "parent_page_id", "page_url"]}),
        ("Task Details", {"fields": ["description", "task_details"]}),
        ("Status & Results", {"fields": ["status", "result", "error_message"]}),
        (
            "Timestamps",
            {"fields": ["notion_updated_at", "created_at", "updated_at", "completed_at"], "classes": ["collapse"]},
        ),
    ]

    def view_page_link(self, obj):
        """Generate a link to view the Notion page."""
        if obj.page_url:
            return format_html('<a href="{}" target="_blank">View Page</a>', obj.page_url)
        return "-"

    view_page_link.short_description = "Page Link"
