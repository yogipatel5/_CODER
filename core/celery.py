"""Celery configuration for the project."""

import logging
import os

from celery import Celery

from core.secrets import secrets_manager

logger = logging.getLogger(__name__)

# Load secrets before configuring Celery
secrets_manager.load_secrets()

# Set up debug logging
logging.basicConfig(level=logging.INFO)

# Load secrets and check what we got
secrets_manager.load_secrets()

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Create Celery app
app = Celery("core")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Debug logging after configuration
logger.debug("Final Celery Configuration:")
logger.debug(f"Broker URL: {app.conf.broker_url}")
logger.debug(f"Result Backend: {app.conf.result_backend}")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
