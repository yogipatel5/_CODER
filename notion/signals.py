import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from notion.models.page import Page
from notion.tasks.page_tasks import process_page_update

logger = logging.getLogger(__name__)

# Fields that trigger embedding updates when modified
EMBEDDING_TRIGGER_FIELDS = {"content", "title", "blocks"}  # Add blocks since it contains the actual page content


@receiver(post_save, sender=Page)
def handle_page_update(sender, instance, created, update_fields, **kwargs):
    """
    Signal handler for Page model updates.
    Triggers the process_page_update task when a page is created or updated.
    Avoids infinite loops by not triggering when only the embedding field is updated.

    One way Flow: Page Update -> Signal Handler -> Task -> Embeddings Service -> Update Embedding (no further triggers)
    """
    logger.info(f"Signal handler triggered for Page {instance.id} - Created: {created}, Update fields: {update_fields}")

    # If only embedding was updated, don't trigger the task to avoid loops
    if update_fields and update_fields == {"embedding"}:
        return

    # Get the list of updated fields
    if update_fields:
        updated_fields = list(update_fields)
    else:
        # If update_fields is None, assume all fields might have changed
        updated_fields = [field.name for field in instance._meta.fields]

    # Check if any of the updated fields should trigger an embedding update
    should_update_embedding = created or any(  # Always update embeddings for new pages
        field in EMBEDDING_TRIGGER_FIELDS for field in updated_fields
    )

    if not should_update_embedding:
        logger.debug(
            f"Skipping embedding update for page {instance.id}: "
            f"no relevant fields were modified. Updated fields: {updated_fields}"
        )
        return

    # Basic validation
    if not instance.content and not instance.title:
        logger.warning(f"Page {instance.id} has no content or title. " "Embeddings will be set to None.")

    # Log the update
    action = "created" if created else "updated"
    logger.info(
        f"Page {instance.id} was {action}. " f"Triggering embedding update task. Modified fields: {updated_fields}"
    )

    # Trigger the Celery task
    process_page_update.delay(page_id=instance.id, updated_fields=updated_fields)
