"""Celery configuration for the project."""

import logging
import os

from celery import Celery

from core.secrets import secrets_manager

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

# Load secrets before anything else
secrets_manager.load_secrets()

# Set up logging
logger = logging.getLogger(__name__)

# Create Celery app
app = Celery("core")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Configure Celery to use the same Redis instance as Django
app.conf.broker_url = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0"
app.conf.result_backend = f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0"

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
