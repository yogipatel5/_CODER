import logging

from celery import group

from notion.services.sync import NotionSyncService
from shared.celery.task import shared_task as scheduled_task

logger = logging.getLogger(__name__)


@scheduled_task(bind=True, max_retries=3)
def sync_pages_task(self):
    """
    Sync all pages from Notion search.
    Uses exponential backoff for retries and will retry up to 3 times.
    """
    try:
        service = NotionSyncService()
        pages = service.client.search_pages("")

        # Initialize progress tracking
        total_pages = len(pages)
        current_progress = 0

        # Track statistics
        stats = {"synced_pages": 0, "skipped_databases": 0, "skipped_database_pages": 0, "skipped_unchanged": 0}

        for page_data in pages:
            # Update progress only if we have a task_id
            current_progress += 1
            if self.request.id:
                self.update_state(
                    state="PROGRESS", meta={"current": current_progress, "total": total_pages, "stats": stats}
                )

            result = service.sync_single_page(page_data)
            if result:
                stats[result] += 1

        logger.info(
            "Synced {synced_pages} pages, skipped {skipped_databases} databases, "
            "{skipped_database_pages} database pages, and {skipped_unchanged} unchanged pages".format(**stats)
        )
        return stats

    except Exception as exc:
        logger.error(f"Error syncing pages: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))  # Exponential backoff


@scheduled_task(bind=True, max_retries=3)
def sync_database_task(self, database_id: str, title: str):
    """
    Sync a single database and its contents from Notion.

    Args:
        database_id: The ID of the database to sync
        title: The title of the database
    """
    try:
        service = NotionSyncService()
        database = service.client.get_database(database_id)
        database_items = service.client.get_database_items(database_id)

        result = service.update_database(
            database_id=database_id, title=title, database=database, database_items=database_items
        )

        logger.info(f"Successfully synced database: {title} ({database_id})")
        return result

    except Exception as exc:
        logger.error(f"Error syncing database {title}: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@scheduled_task(
    bind=True,
    schedule={
        "type": "interval",
        "every": 1,
        "period": "minutes",
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
    2. For the project page, sync all its child databases

    The task is scheduled to run every minute and coordinates the sync process.
    """
    try:
        service = NotionSyncService()
        project_page_id = service.get_project_page_id()

        # Start pages sync first
        sync_pages_task.delay()

        if not project_page_id:
            return {"status": "Initiated sync for pages only (no project page found)", "database_count": 0}

        blocks = service.client.get_block_children(project_page_id)
        database_blocks = [b for b in blocks if b.get("type") == "child_database"]
        database_count = len(database_blocks)

        if database_count > 0:
            # Create database sync tasks group
            database_tasks = group(
                [sync_database_task.s(block["id"], block["child_database"]["title"]) for block in database_blocks]
            )
            # Execute database tasks
            database_tasks.delay()
            logger.info(f"Starting sync for {database_count} databases")

        return {"status": f"Initiated sync for pages and {database_count} databases", "database_count": database_count}

    except Exception as exc:
        logger.error(f"Error in sync workflow: {exc}", exc_info=True)
        raise self.retry(exc=exc)
