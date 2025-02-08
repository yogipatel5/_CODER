"""Celery settings configuration."""

import os

from kombu import Exchange, Queue

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

# Enable task events
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_WORKER_SEND_TASK_EVENTS = True

# Default queue configuration
CELERY_DEFAULT_QUEUE = "default"
CELERY_DEFAULT_EXCHANGE = "default"
CELERY_DEFAULT_ROUTING_KEY = "default"

# App-specific configurations for Celery
CELERY_APP_CONFIGS = {
    "pfsense": {
        "task_options": {
            "retry_backoff": True,
            "max_retries": 3,
            "acks_late": True,
        },
    },
    "notion": {
        "task_options": {
            "retry_backoff": True,
            "max_retries": 5,  # More retries for external API calls
            "acks_late": True,
            "rate_limit": "100/m",  # Rate limit for API calls
        },
    },
    "print": {
        "task_options": {
            "retry_backoff": True,
            "max_retries": 3,
            "acks_late": True,
        },
    },
}

# Create default queue
CELERY_QUEUES = (
    Queue(
        CELERY_DEFAULT_QUEUE,
        Exchange(CELERY_DEFAULT_EXCHANGE, type="direct"),
        routing_key=CELERY_DEFAULT_ROUTING_KEY,
    ),
)

# Configure task routing using our dynamic router
CELERY_TASK_ROUTES = ("shared.celery.router.DjangoAppRouter",)

# Additional Celery settings for better task handling
CELERY_TASK_TRACK_STARTED = True  # Track when tasks are started
CELERY_TASK_TIME_LIMIT = 60 * 60  # 1 hour task time limit
CELERY_TASK_SOFT_TIME_LIMIT = 50 * 60  # Soft limit 50 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Disable prefetching for better task distribution
