"""
Command to create a Notion page.
"""

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Create a new page in Notion"

    def add_arguments(self, parser):
        parser.add_argument("parent_id", help="ID of the parent (page/database) or 'workspace'")
        parser.add_argument("title", help="Title of the new page")
        parser.add_argument(
            "--parent-type",
            choices=["page_id", "database_id", "workspace"],
            default="page_id",
            help="Type of parent (default: page_id)",
        )
        parser.add_argument("--properties", nargs="*", help="Additional properties in format key=value")

    def handle(self, *args, **options):
        parent_id = options["parent_id"]
        title = options["title"]
        parent_type = options["parent_type"]

        # For workspace parent, use a dummy ID that will be ignored
        if parent_type == "workspace":
            parent_id = "workspace"

        properties = {}
        if options.get("properties"):
            for prop in options["properties"]:
                key, value = prop.split("=", 1)
                properties[key] = {"rich_text": [{"text": {"content": value}}]}

        try:
            page = self.api.create_page(parent_id, title, properties, parent_type)
            self.stdout.write(self.style.SUCCESS(f"Created page with ID: {page['id']}"))
            return page["id"]  # Return the ID for use in scripts
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating page: {e}"))
