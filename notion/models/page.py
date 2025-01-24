from django.db import models

from notion.managers.page import PageManager


class Page(models.Model):
    """Model representing a Notion page."""

    objects = PageManager()

    id = models.CharField(max_length=255, primary_key=True)
    created_time = models.DateTimeField()
    last_edited_time = models.DateTimeField()

    # created_by = models.ForeignKey(
    #     "notion.User", related_name="created_pages", on_delete=models.SET_NULL, null=True, blank=True
    # )
    # last_edited_by = models.ForeignKey(
    #     "notion.User", related_name="edited_pages", on_delete=models.SET_NULL, null=True, blank=True
    # )

    cover = models.TextField(null=True, blank=True)  # Could be an image or file
    icon = models.CharField(max_length=50, null=True, blank=True)  # emoji

    archived = models.BooleanField(default=False)
    in_trash = models.BooleanField(default=False)

    title = models.CharField(max_length=255)
    url = models.URLField()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Notion Page"
        verbose_name_plural = "Notion Pages"
