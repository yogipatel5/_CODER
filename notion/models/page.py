from django.db import models
from pgvector.django import VectorField

from notion.managers import PageManager


class Page(models.Model):
    """Model representing a Notion page."""

    objects = PageManager()

    # TODO: Move complex property handling to PageManager
    # TODO: Add proper validation for parent_type choices
    # TODO: Consider moving JSON schema validation to a separate service
    id = models.CharField(max_length=36, primary_key=True)
    created_time = models.DateTimeField()
    last_edited_time = models.DateTimeField()
    last_synced_at = models.DateTimeField(auto_now=True)

    content = models.TextField(null=True, blank=True, help_text="Cleaned text content for embeddings")
    embedding = VectorField(dimensions=384, null=True, blank=True, help_text="Vector embedding of the content")
    search_metadata = models.JSONField(default=dict, help_text="Metadata for search optimization")

    cover = models.JSONField(null=True, blank=True)  # Could be an image or file
    icon = models.JSONField(null=True, blank=True)  # Contains type and emoji data

    parent_type = models.CharField(max_length=50, default="workspace")  # e.g., "workspace", "page", etc.
    parent_id = models.CharField(max_length=255, null=True, blank=True)

    archived = models.BooleanField(default=False)
    in_trash = models.BooleanField(default=False)

    title = models.CharField(max_length=255)
    url = models.URLField()
    public_url = models.URLField(null=True, blank=True)
    raw_properties = models.JSONField(default=dict)
    blocks = models.JSONField(default=list, help_text="Page content blocks from Notion")  # New field for content

    class Meta:
        verbose_name = "Notion Page"
        verbose_name_plural = "Notion Pages"
        db_table = "notion_page"
        indexes = [
            models.Index(fields=["title"]),
        ]

    def __str__(self):
        return self.title

    @property
    def plain_title(self) -> str:
        """Extract plain text title from properties."""
        if not self.raw_properties or "title" not in self.raw_properties:
            return self.title

        title_blocks = self.raw_properties["title"].get("title", [])
        return " ".join(block.get("plain_text", "") for block in title_blocks)

    def save(self, *args, **kwargs):
        """Override save to ensure title is set from properties if needed."""
        if not self.title and self.raw_properties:
            self.title = self.plain_title
        super().save(*args, **kwargs)
