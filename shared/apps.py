"""shared Django app configuration."""

from django.apps import AppConfig


class SharedConfig(AppConfig):
    """Django app configuration for shared."""

    name = "shared"
    verbose_name = "Shared"
