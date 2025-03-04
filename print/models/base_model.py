"""Base model for print."""

from django.db import models

from print.managers.base_manager import BaseManager


class BaseModel(models.Model):
    """Abstract base model with common fields and methods."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    objects = BaseManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self):
        """Return string representation."""
        if hasattr(self, "name"):
            return self.name
        return f"{self.__class__.__name__}({self.id})"

    def soft_delete(self):
        """Soft delete the object."""
        self.is_active = False
        self.save()
