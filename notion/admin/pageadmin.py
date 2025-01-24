from django.contrib import admin
from django.utils.html import format_html

from notion.models.page import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Admin interface for Page model."""

    list_display = ("title", "id", "last_edited_time", "last_synced_at", "content_preview")
    list_filter = ("parent_type", "last_edited_time", "last_synced_at")
    search_fields = ("title", "id", "parent_id")
    readonly_fields = ("id", "last_edited_time", "last_synced_at", "raw_properties", "blocks", "content_preview")
    ordering = ("-last_edited_time",)

    def content_preview(self, obj):
        """Show a preview of the page content."""
        if not obj.blocks:
            return "-"

        preview_text = []
        for block in obj.blocks[:3]:  # Show first 3 blocks
            if block.get("type") == "paragraph":
                text = block.get("paragraph", {}).get("rich_text", [])
                preview_text.append(" ".join(t.get("plain_text", "") for t in text))

        preview = " ".join(preview_text)
        if len(preview) > 100:
            preview = preview[:97] + "..."

        return format_html("<span title='{}'>{}</span>", preview, preview)

    content_preview.short_description = "Content Preview"
