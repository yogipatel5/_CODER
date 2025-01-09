"""
Command to delete (archive) a Notion page.
"""

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Delete (archive) a Notion page"

    def add_arguments(self, parser):
        parser.add_argument("page_id", help="ID of the page to delete")

    def handle(self, *args, **options):
        page_id = options["page_id"]

        try:
            page = self.api.delete_page(page_id)
            self.stdout.write(self.style.SUCCESS(f"Deleted page: {self.get_title_from_page(page)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error deleting page: {e}"))
