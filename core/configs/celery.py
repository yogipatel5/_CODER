"""Celery settings configuration."""

import os

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0")
CELERY_RESULT_BACKEND = os.getenv(
    "CELERY_RESULT_BACKEND", f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/0"
)

CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "America/New_York")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
