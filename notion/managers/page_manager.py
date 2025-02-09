from django.db import models

from notion.services.markdown import MarkdownService


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

    def get_page(self, page_id: str):
        """Get page by ID."""
        return self.get(id=page_id)  # Using id since it's defined as primary_key in the model

    def get_page_markdown(self, page_id: str) -> str:
        """
        Get page content in markdown format.

        Args:
            page_id: The ID of the page to convert

        Returns:
            str: The page content in markdown format
        """
        page = self.get_page(page_id)
        markdown_service = MarkdownService()
        return markdown_service.convert_blocks_to_markdown(page.blocks)
