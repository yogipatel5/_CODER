import logging

from django.contrib import admin
from django.utils.html import escape

from notion.models.page import Page
from notion.services.markdown import MarkdownService

logger = logging.getLogger(__name__)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Admin interface for Page model."""

    list_display = ("title", "id", "last_edited_time", "last_synced_at", "content_preview")
    list_filter = ("parent_type", "last_edited_time", "last_synced_at")
    search_fields = ("title", "id", "parent_id")
    readonly_fields = (
        "id",
        "last_edited_time",
        "last_synced_at",
        "raw_properties",
        "content_preview",
        "markdown_content",
        "blocks",
    )
    ordering = ("-last_edited_time",)

    def content_preview(self, obj):
        """Show a preview of the page content."""
        if not obj.blocks:
            return "-"

        # Convert blocks to markdown
        markdown_service = MarkdownService()
        markdown_content = markdown_service.convert_blocks_to_markdown(obj.blocks)

        # Return a truncated preview
        max_length = 200
        preview = markdown_content[:max_length] + "..." if len(markdown_content) > max_length else markdown_content
        return escape(preview)

    content_preview.short_description = "Content Preview"

    def markdown_content(self, obj):
        """Show the full markdown content of the page."""
        markdown_content = Page.objects.get_page_markdown(obj.id)
        return markdown_content

    markdown_content.short_description = "Markdown Content"
