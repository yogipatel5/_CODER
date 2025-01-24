"""Test Celery Task see if its autodiscover works."""
import logging

from celery import shared_task
from django.apps import apps
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def test_task(self):
    """Test Celery Task see if its autodiscover works."""

    return True
