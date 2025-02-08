import logging
from datetime import datetime

from celery import shared_task
from django.conf import settings

from notion.api.client import NotionClient
from notion.models.database import Database
from shared.celery.task import shared_task

logger = logging.getLogger(__name__)


# TODO: Move database operations to DatabaseManager class
# TODO: Add proper test coverage for sync functionality
@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def sync_database(self, database_id: str, title: str):
    """
    Sync a specific Notion database.
    This task is called for each database to parallelize the work.
    """
    try:
        client = NotionClient()
        database = client.get_database(database_id)
        database_items = client.query_database(database_id)

        # Parse timestamps
        created_time = datetime.fromisoformat(database["created_time"].replace("Z", "+00:00"))
        last_edited_time = datetime.fromisoformat(database["last_edited_time"].replace("Z", "+00:00"))

        # Create or update database
        db, created = Database.objects.update_or_create(
            id=database_id,
            defaults={
                "title": title,
                "parent_page_id": settings.NOTION_PROJECT_PAGE_ID.replace("-", ""),
                "created_time": created_time,
                "last_edited_time": last_edited_time,
                "properties_schema": database.get("properties", {}),
                "rows": database_items,
            },
        )

        return {"database_id": database_id, "rows_count": len(database_items)}
    except Exception as exc:
        logger.error(f"Error syncing database {title} ({database_id}): {exc}", exc_info=True)
        raise self.retry(exc=exc)
