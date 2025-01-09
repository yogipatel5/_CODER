"""
Command to update a Notion page.
"""

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Update properties of a Notion page"

    def add_arguments(self, parser):
        parser.add_argument("page_id", help="ID of the page to update")
        parser.add_argument("--properties", nargs="*", help="Properties to update in format key=value")

    def handle(self, *args, **options):
        page_id = options["page_id"]
        properties = {}

        if options.get("properties"):
            for prop in options["properties"]:
                key, value = prop.split("=", 1)
                if key == "title":
                    properties[key] = {"title": [{"text": {"content": value}}]}
                else:
                    properties[key] = {"rich_text": [{"text": {"content": value}}]}

        try:
            page = self.api.update_page(page_id, properties)
            self.stdout.write(self.style.SUCCESS(f"Updated page: {self.get_title_from_page(page)}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error updating page: {e}"))
