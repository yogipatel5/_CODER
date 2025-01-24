"""Tasks for processing Notion agent jobs."""
import logging

from celery import shared_task
from services.notey import NoteyService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_pending_jobs(self):
    """Process all pending Notion agent jobs."""
    NoteyService()

    pass

    return True
