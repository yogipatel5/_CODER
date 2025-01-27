from django.db.models.signals import post_save
from django.dispatch import receiver

from notion.models import Page
from notion.tasks.page_tasks import process_page_update


@receiver(post_save, sender=Page)
def handle_page_update(sender, instance, created, update_fields, **kwargs):
    """
    Signal handler for Page model updates.
    Triggers the process_page_update task when a page is created or updated.
    Avoids infinite loops by not triggering when only the embedding field is updated.

    One way Flow: Page Update -> Signal Handler -> Task -> Embeddings Service -> Update Embedding (no further triggers)
    """
    # If only embedding was updated, don't trigger the task to avoid loops
    if update_fields and update_fields == {"embedding"}:
        return

    # Get the list of updated fields
    if update_fields:
        updated_fields = list(update_fields)
    else:
        # If update_fields is None, assume all fields might have changed
        updated_fields = [field.name for field in instance._meta.fields]

    # Trigger the Celery task
    process_page_update.delay(page_id=instance.id, updated_fields=updated_fields)
