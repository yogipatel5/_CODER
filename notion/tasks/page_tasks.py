from celery import shared_task
from celery.utils.log import get_task_logger

from notion.services.embeddings import EmbeddingsService

logger = get_task_logger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minute
    autoretry_for=(Exception,),
    retry_backoff=True,
)
def process_page_update(self, page_id, updated_fields):
    """
    Process updates to a Notion page.

    This task is triggered whenever a Page model is updated. It handles any necessary
    post-update processing such as updating embeddings via the EmbeddingsService.

    Args:
        page_id (str): The ID of the updated page
        updated_fields (list): List of fields that were updated
    """
    from notion.models import Page

    try:
        page = Page.objects.get(id=page_id)
        logger.info(f"Processing update for page {page_id}, updated fields: {updated_fields}")

        # If content was updated, update embeddings
        if "content" in updated_fields:
            embeddings_service = EmbeddingsService()
            embeddings_service.update_page_embeddings(page)
            logger.info(f"Updated embeddings for page {page_id}")

        return {"status": "success", "page_id": page_id, "processed_fields": updated_fields}

    except Page.DoesNotExist:
        logger.error(f"Page {page_id} not found")
        raise
    except Exception as exc:
        logger.error(f"Error processing page update: {exc}")
        raise
