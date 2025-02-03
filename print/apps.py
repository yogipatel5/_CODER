import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class PrintConfig(AppConfig):
    name = "print"
    verbose_name = "Print"

    def ready(self):
        """
        Initialize the app. This method is called by Django after the app is loaded.
        """
        pass  # All discovery is now handled by __init__.py files
