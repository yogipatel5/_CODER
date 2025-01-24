from django.db import models


class PageManager(models.Manager):
    """Manager for Page model."""

    def get_active_pages(self):
        """Get all non-archived and non-trashed pages."""
        return self.filter(archived=False, in_trash=False)

    def get_archived_pages(self):
        """Get all archived pages."""
        return self.filter(archived=True)

    def get_trashed_pages(self):
        """Get all pages in trash."""
        return self.filter(in_trash=True)
