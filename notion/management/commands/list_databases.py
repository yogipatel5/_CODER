"""
Command to list Notion databases.
"""

import json
from typing import Any, Dict

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "List all accessible Notion databases"

    def format_database_data(self, database: Dict[str, Any]) -> Dict[str, Any]:
        """Format a database for the response."""
        # Extract title from title property
        title = "Untitled"
        if "title" in database:
            title_parts = []
            for text in database["title"]:
                if "text" in text and "content" in text["text"]:
                    title_parts.append(text["text"]["content"])
            if title_parts:
                title = "".join(title_parts)

        parent = database.get("parent", {})
        parent_type = parent.get("type", "unknown")
        parent_title = "Unknown"
        parent_id = "unknown"

        # Get the correct parent ID and title
        if parent_type == "workspace":
            parent_id = "workspace"
            parent_title = "Workspace"
        elif parent_type == "page_id":
            parent_id = parent.get("page_id", "unknown")
            try:
                if parent_id:
                    parent_page = self.api.get_page(parent_id)
                    parent_title = self.get_title_from_page(parent_page)
            except Exception:
                pass

        return {
            "id": database["id"],
            "title": title,
            "parent": {"type": parent_type, "id": parent_id, "title": parent_title},
            "url": database.get("url"),
            "created_time": database.get("created_time"),
            "last_edited_time": database.get("last_edited_time"),
            "properties": database.get("properties", {}),
        }

    def handle(self, *args, **options):
        response = {
            "success": False,
            "message": "",
            "context": "",
            "data": {"databases": [], "total": 0},
            "progress": [],
        }

        try:
            # Get all databases
            databases = self.api.list_databases()

            if not databases:
                response.update({"success": True, "message": "No databases found"})
                self.stdout.write(json.dumps(response, indent=2))
                return

            # Format the response
            formatted_databases = [self.format_database_data(db) for db in databases]
            response.update(
                {
                    "success": True,
                    "message": f"Found {len(databases)} databases",
                    "data": {"databases": formatted_databases, "total": len(databases)},
                }
            )

        except Exception as e:
            response.update({"message": "Error listing databases", "error": str(e)})

        self.stdout.write(json.dumps(response, indent=2))
