"""Django app configuration for pfsense app."""

from django.apps import AppConfig


class PfsenseConfig(AppConfig):
    """Configuration for pfsense app."""

    name = "pfsense"
    verbose_name = "Pfsense"

    def ready(self):
        """Import tasks to ensure they are registered with Celery."""
        import pfsense.tasks  # noqa
