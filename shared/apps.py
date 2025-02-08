"""shared Django app configuration."""

import logging

from django.apps import AppConfig, apps
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)


class SharedConfig(AppConfig):
    """Django app configuration for shared."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "shared"
    verbose_name = "Shared"

    def ready(self):
        """Initialize the application."""
        # Import task module to register signal handlers
        from shared.celery.task import initialize_periodic_tasks

        # Connect signal handler to all apps
        for app_config in apps.get_app_configs():
            # logger.info(f"Connecting post_migrate signal for app: {app_config.label}")
            post_migrate.connect(initialize_periodic_tasks, sender=app_config)
