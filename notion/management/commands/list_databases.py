"""
Command to list Notion databases.
"""

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "List all accessible Notion databases"

    def handle(self, *args, **options):
        databases = self.api.list_databases()
        if not databases:
            self.stdout.write("No databases found.")
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(databases)} databases:"))
        for db in databases:
            title = db.get("title", [{}])[0].get("text", {}).get("content", "Untitled")
            self.stdout.write(f"- {title} (ID: {db['id']})")
