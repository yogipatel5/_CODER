from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.utils import timezone

from notion.services.embeddings import EmbeddingsService

logger = get_task_logger(__name__)


def get_task_status_key(page_id):
    """Generate a cache key for storing task status."""
    return f"page_embedding_status:{page_id}"


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,  # Max 5 minutes between retries
    retry_jitter=True,  # Add randomness to retry delays
)
def process_page_update(self, page_id, updated_fields):
    """
    Process updates to a Notion page.

    This task is triggered whenever a Page model is updated. It handles any necessary
    post-update processing such as updating embeddings via the EmbeddingsService.

    Args:
        page_id (str): The ID of the updated page
        updated_fields (list): List of fields that were updated

    Returns:
        dict: Task result containing status and details
    """
    from notion.models.page import Page

    status_key = get_task_status_key(page_id)
    status = {
        "task_id": self.request.id,
        "status": "processing",
        "start_time": timezone.now().isoformat(),
        "retries": self.request.retries,
        "updated_fields": updated_fields,
    }
    cache.set(status_key, status, timeout=3600)  # Store status for 1 hour

    try:
        page = Page.objects.get(id=page_id)
        logger.info(f"Processing update for page {page_id}, updated fields: {updated_fields}")

        # If content was updated, update embeddings
        if "content" in updated_fields or "title" in updated_fields:
            embeddings_service = EmbeddingsService()
            embeddings_service.update_page_embeddings(page)
            logger.info(f"Updated embeddings for page {page_id}")

        status.update(
            {
                "status": "success",
                "end_time": timezone.now().isoformat(),
                "error": None,
            }
        )
        cache.set(status_key, status, timeout=3600)

        return {
            "status": "success",
            "page_id": page_id,
            "processed_fields": updated_fields,
            "retries": self.request.retries,
        }

    except Page.DoesNotExist:
        error_msg = f"Page {page_id} not found"
        logger.error(error_msg)
        status.update(
            {
                "status": "error",
                "end_time": timezone.now().isoformat(),
                "error": error_msg,
            }
        )
        cache.set(status_key, status, timeout=3600)
        raise

    except Exception as exc:
        error_msg = f"Error processing page update: {exc}"
        logger.error(error_msg)
        status.update(
            {
                "status": "error",
                "end_time": timezone.now().isoformat(),
                "error": error_msg,
            }
        )
        cache.set(status_key, status, timeout=3600)
        raise
