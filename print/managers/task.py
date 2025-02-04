from .base_manager import BaseManager


class TaskManager(BaseManager):
    """Manager for Task model."""

    def get_queryset(self):
        return super().get_queryset().select_related("periodic_task")
