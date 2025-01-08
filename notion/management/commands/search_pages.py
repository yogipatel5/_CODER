"""
Command to search Notion pages.
"""

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Search for pages in Notion"

    def add_arguments(self, parser):
        parser.add_argument("query", help="Search query")

    def handle(self, *args, **options):
        pages = self.api.search_pages(options["query"])
        if not pages:
            self.stdout.write("No pages found.")
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(pages)} pages:"))
        for page in pages:
            title = self.get_title_from_page(page)
            self.stdout.write(f"- {title} (ID: {page['id']})")
