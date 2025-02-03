from django.db import models


class BaseManager(models.Manager):
    """Base manager for all models in the app."""

    def get_queryset(self):
        return super().get_queryset()

    def active(self):
        """Return only active objects."""
        return self.get_queryset().filter(is_active=True)
