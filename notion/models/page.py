from django.db import models
from django.db.models import JSONField

from notion.managers.page import PageManager


class Page(models.Model):
    """Model representing a Notion page."""

    objects = PageManager()

    # TODO: Move complex property handling to PageManager
    # TODO: Add proper validation for parent_type choices
    # TODO: Consider moving JSON schema validation to a separate service
    id = models.CharField(max_length=255, primary_key=True)
    created_time = models.DateTimeField()
    last_edited_time = models.DateTimeField()
    last_synced_at = models.DateTimeField(auto_now=True)

    content = models.TextField(blank=True, help_text="Cleaned text content for embeddings")
    embedding = models.JSONField(null=True, blank=True, help_text="Vector embedding of the content", db_index=True)
    search_metadata = JSONField(default=dict, help_text="Metadata for search optimization")

    cover = JSONField(null=True, blank=True)  # Could be an image or file
    icon = JSONField(null=True, blank=True)  # Contains type and emoji data

    parent_type = models.CharField(max_length=50, default="workspace")  # e.g., "workspace", "page", etc.
    parent_id = models.CharField(max_length=255, null=True, blank=True)

    archived = models.BooleanField(default=False)
    in_trash = models.BooleanField(default=False)

    title = models.CharField(max_length=255)
    url = models.URLField()
    public_url = models.URLField(null=True, blank=True)
    raw_properties = JSONField(default=dict)
    blocks = JSONField(default=list, help_text="Page content blocks from Notion")  # New field for content

    class Meta:
        indexes = [models.Index(fields=["embedding"], name="notion_page_embedding_idx", opclasses=["vector_ops"])]

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

    class Meta:
        verbose_name = "Notion Page"
        verbose_name_plural = "Notion Pages"
