"""shared Django app configuration."""

from django.apps import AppConfig


class SharedConfig(AppConfig):
    """Django app configuration for shared."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "shared"
    verbose_name = "Shared"
