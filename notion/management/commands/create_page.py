"""
Command to create a Notion page.
"""

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Create a new page in a Notion database"

    def add_arguments(self, parser):
        parser.add_argument("database_id", help="ID of the parent database")
        parser.add_argument("title", help="Title of the new page")
        parser.add_argument("--properties", nargs="*", help="Additional properties in format key=value")

    def handle(self, *args, **options):
        properties = {}
        if options.get("properties"):
            for prop in options["properties"]:
                key, value = prop.split("=", 1)
                properties[key] = {"rich_text": [{"text": {"content": value}}]}

        page = self.api.create_page(options["database_id"], options["title"], properties)
        self.stdout.write(self.style.SUCCESS(f"Created page with ID: {page['id']}"))
