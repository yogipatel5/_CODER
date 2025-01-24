"""Tasks for scanning Notion pages."""

import logging
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from django.utils import timezone
from services.notion import NotionService

from notion.models.notionagentjobs import NotionAgentJob
from notion.models.task import Task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def scan_notion_for_notey_blocks() -> List[str]:
    """
    Scan Notion pages for blocks containing 'Notey' and create agent jobs.

    Returns:
        List[str]: List of created job IDs
    """
    logger.debug("Starting Notion scanning task")

    try:
        # Get task configuration
        task = Task.objects.get_or_create(
            name="scan_notion_for_notey_blocks",
            defaults={"active": True, "last_run": timezone.now()},
        )[0]
        logger.debug(f"Retrieved task configuration: active={task.active}")

        if not task.active:
            logger.info("Task is not active, skipping")
            return []

        logger.debug("Updating task last run time")
        task.last_run = timezone.now()
        task.save()

        # Initialize Notion service
        logger.debug("Initializing NotionService")
        notion_service = NotionService()

        # Get last checked time
        logger.debug("Getting last checked time from task config")
        last_checked = task.last_checked or timezone.now() - timedelta(days=7)  # Default to 7 days ago
        logger.debug(f"Last checked time: {last_checked}")

        # Get all pages
        pages = notion_service.get_recent_pages()
        logger.debug(f"Processing {len(pages)} pages")

        jobs = []
        for page in pages:
            try:
                page_id = page.get("id")
                last_edited = timezone.make_aware(datetime.fromisoformat(page.get("last_edited_time").rstrip("Z")))

                # Debug logging for time comparison
                logger.debug(
                    f"Processing page {page_id}:\n"
                    f"  Title: {page.get('properties', {}).get('title')}\n"
                    f"  URL: {page.get('url')}\n"
                    f"  Created Time: {page.get('created_time')}\n"
                    f"  Last Edited: {last_edited}"
                )

                # Get and check page content
                page_content = notion_service.get_page_content(page_id)
                notey_text = notion_service.has_notey_content(page_content)

                if notey_text:
                    # Check if we already have a pending job for this page with the same content
                    existing_job = NotionAgentJob.objects.filter(
                        page_id=page_id,
                        task_details=notey_text,  # Only create new job if content changed
                        status=NotionAgentJob.Status.PENDING,
                    ).first()

                    if existing_job:
                        logger.debug(f"Skipping page {page_id} - already has a pending job with same content")
                        continue

                    logger.debug(f"Creating job for page {page_id} with Notey task: {notey_text}")
                    parent = page.get("parent", {})
                    parent_id = parent.get("page_id") or parent.get("database_id")

                    # Get page title for description
                    title = page.get("properties", {}).get("title", {})
                    if isinstance(title, dict):
                        title = title.get("title", [{"plain_text": "Untitled"}])[0].get("plain_text", "Untitled")

                    job = notion_service.create_agent_job(
                        page_id=page_id,
                        parent_page_id=parent_id,
                        last_edited=last_edited,
                        description=f"Page: {title}",
                        task_details=notey_text,
                    )
                    jobs.append(job)
                    logger.info(f"Created job for page {page_id}")

            except Exception as e:
                logger.error(f"Error processing page {page_id}: {str(e)}", exc_info=True)
                continue

        # Update last checked time
        logger.debug(f"Updating last checked time to {timezone.now()}")
        task.last_checked = timezone.now()
        task.save()

        if not jobs:
            logger.info("No new Notey blocks found during scan")
        else:
            logger.info(f"Found {len(jobs)} new Notey blocks")

        logger.debug("Notion scanning task completed successfully")
        return [str(job.id) for job in jobs]

    except Exception as e:
        logger.error(f"Error scanning Notion: {str(e)}", exc_info=True)
        raise
