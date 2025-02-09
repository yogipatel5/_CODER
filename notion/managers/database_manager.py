from django.db import models


class DatabaseManager(models.Manager):
    """Manager for Database model."""

    def get_project_databases(self, project_page_id):
        """Get all databases that belong to a specific project page."""
        return self.filter(parent_page_id=project_page_id)

    def get_database_by_title(self, project_page_id, title):
        """Get a database by its title within a project."""
        return self.filter(parent_page_id=project_page_id, title=title).first()
