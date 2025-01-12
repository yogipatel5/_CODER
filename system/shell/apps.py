"""Django app configuration for the Notion integration."""

from django.apps import AppConfig


class NotionConfig(AppConfig):
    """Notion app config"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "notion"
