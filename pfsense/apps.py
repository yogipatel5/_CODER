"""pfsense Django app configuration."""

from django.apps import AppConfig


class PfsenseConfig(AppConfig):
    """Django app configuration for pfsense."""

    name = "pfsense"
    verbose_name = "Pfsense"

    def ready(self):
        """Import tasks to ensure they are registered."""
        # Import tasks to ensure they are registered with Celery
        from pfsense.tasks import sync_dhcp_routes  # noqa
