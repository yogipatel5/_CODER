import logging

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# Example signal handler setup:
"""
from print.models.your_model import YourModel
from print.tasks.your_tasks import your_task

@receiver(post_save, sender=YourModel)
def handle_model_save(sender, instance, created, update_fields, **kwargs):
    \"""
    Signal handler for YourModel updates.
    Triggers appropriate tasks or updates when the model is created or modified.
    \"""
    logger.info(f"Signal handler triggered for YourModel {instance.id} - Created: {created}")

    # Example: Trigger a task on model update
    your_task.delay(model_id=instance.id)
"""
