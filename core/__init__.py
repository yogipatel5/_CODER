"""Core module initialization."""

from .celery import app as celery

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
__all__ = ("celery",)
