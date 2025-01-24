from django.db import models
from django.utils import timezone

from ..managers.notionagentjob import NotionAgentJobManager


class NotionAgentJob(models.Model):
    """Model to track Notion agent jobs and their tasks."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    # Page identification
    page_id = models.CharField(max_length=255, help_text="Unique identifier of the Notion page")
    parent_page_id = models.CharField(
        max_length=255, null=True, blank=True, help_text="ID of the parent page in Notion (if any)"
    )
    page_url = models.URLField(max_length=1024, help_text="URL of the Notion page")

    # Task details
    description = models.TextField(help_text="Brief description of the page")
    task_details = models.TextField(help_text="Details of what needs to be done")

    # Status tracking
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, help_text="Current status of the task"
    )
    error_message = models.TextField(blank=True, help_text="Error message if the task failed")
    result = models.TextField(blank=True, help_text="Results or changes made")

    # Timestamps
    notion_updated_at = models.DateTimeField(help_text="When the page was last updated in Notion")
    created_at = models.DateTimeField(default=timezone.now, help_text="When the task was created")
    updated_at = models.DateTimeField(auto_now=True, help_text="When the task was last updated")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When the task was completed or failed")

    # Manager
    objects = NotionAgentJobManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["page_id"]),
            models.Index(fields=["parent_page_id"]),
        ]

    def __str__(self):
        return f"NotionAgentJob - Page: {self.page_id} ({self.status})"
