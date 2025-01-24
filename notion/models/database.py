from django.db import models
from django.db.models import JSONField

from notion.managers.database import DatabaseManager


class Database(models.Model):
    """Model representing a Notion database."""

    # TODO: Add schema validation for properties_schema
    # TODO: Add methods for row manipulation in DatabaseManager
    # TODO: Implement versioning for schema changes
    # TODO: Add support for database relations
    objects = DatabaseManager()

    id = models.CharField(max_length=255, primary_key=True)
    created_time = models.DateTimeField()
    last_edited_time = models.DateTimeField()
    last_synced_at = models.DateTimeField(auto_now=True)

    content = models.TextField(blank=True, help_text="Cleaned text content for embeddings")
    embedding = models.JSONField(null=True, blank=True, help_text="Vector embedding of the content")
    search_metadata = JSONField(default=dict, help_text="Metadata for search optimization")

    title = models.CharField(max_length=255)
    parent_page_id = models.CharField(max_length=255)
    properties_schema = JSONField(default=dict, help_text="Schema of database properties")
    rows = JSONField(default=list, help_text="Database rows/items")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Notion Database"
        verbose_name_plural = "Notion Databases"
