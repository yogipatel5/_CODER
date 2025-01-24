from celery import shared_task
from celery.utils.log import get_task_logger

from notion.services.sync_service import NotionSyncService

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
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
