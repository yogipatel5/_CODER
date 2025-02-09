from django.contrib import admin
from django.utils.html import format_html

from notion.models import Database


@admin.register(Database)
class DatabaseAdmin(admin.ModelAdmin):
    """Admin interface for Database model."""

    # TODO: Add custom actions for manual sync trigger
    # TODO: Add JSON viewer for properties_schema and rows
    # TODO: Add filtering by database schema properties
    # TODO: Add bulk operations support
    list_display = ("title", "id", "parent_page_id", "last_edited_time", "last_synced_at", "row_count")
    list_filter = ("last_edited_time", "last_synced_at")
    search_fields = ("title", "id", "parent_page_id")
    readonly_fields = ("id", "created_time", "last_edited_time", "last_synced_at", "properties_schema", "rows")
    ordering = ("-last_edited_time",)

    def row_count(self, obj):
        """Show number of rows in the database."""
        count = len(obj.rows)
        return format_html("<span>{} rows</span>", count)

    row_count.short_description = "Row Count"
