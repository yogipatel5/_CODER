import logging

from notion.services.sync import NotionSyncService
from shared.celery.task import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    schedule={
        "type": "interval",
        "every": 1,
        "period": "minutes",  # Use lowercase for timedelta
    },
    description="Sync Notion content",
    notify_on_error=True,
    disable_on_error=False,
    max_retries=3,
)
def sync_notion_content(self):
    """
    Sync both pages and databases from Notion.
    This task will:
    1. Sync all pages from Notion search
    2. For the project page, sync all its child databases in parallel

    The task uses exponential backoff for retries and will retry up to 3 times
    with a 1-minute delay between retries.
    """
    try:
        service = NotionSyncService()
        result = service.sync_all()
        logger.info("Successfully synced Notion content")
        return result
    except Exception as exc:
        logger.error(f"Error syncing Notion content: {exc}", exc_info=True)
        raise self.retry(exc=exc)
