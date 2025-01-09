"""
Command to list Notion pages.
"""

import json
from typing import Any, Dict

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "List all accessible Notion pages"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            help="Database ID to filter pages from a specific database",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of pages to return (default: 100)",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output in JSON format (default)",
        )

    def format_page_data(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Format a page for the response."""
        title = self.get_title_from_page(page)
        parent = page.get("parent", {})
        parent_type = parent.get("type", "unknown")

        # Get the correct parent ID based on the parent type
        if parent_type == "workspace":
            parent_id = "workspace"
        elif parent_type == "page_id":
            parent_id = parent.get("page_id", "unknown")
        elif parent_type == "database_id":
            parent_id = parent.get("database_id", "unknown")
        else:
            parent_id = "unknown"

        return {
            "id": page["id"],
            "title": title,
            "parent": {
                "type": parent_type,
                "id": parent_id,
            },
            "url": page.get("url"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
        }

    def handle(self, *args, **options):
        response = {
            "success": False,
            "message": "",
            "context": "",
            "data": {
                "pages": [],
                "total": 0,
                "limit": options["limit"],
            },
            "progress": [],
        }

        try:
            # Using search with empty query to list all pages
            pages = self.api.search_pages("")

            if not pages:
                response.update(
                    {
                        "success": True,
                        "message": "No pages found",
                    }
                )
                self.stdout.write(json.dumps(response, indent=2))
                return

            # Filter by database if specified
            if options.get("database"):
                pages = [page for page in pages if page.get("parent", {}).get("database_id") == options["database"]]

            # Apply limit
            pages = pages[: options["limit"]]

            # Format the response
            formatted_pages = [self.format_page_data(page) for page in pages]
            response.update(
                {
                    "success": True,
                    "message": f"Found {len(pages)} pages",
                    "data": {
                        "pages": formatted_pages,
                        "total": len(pages),
                        "limit": options["limit"],
                    },
                }
            )

        except Exception as e:
            response.update({"message": "Error listing pages", "error": str(e)})

        self.stdout.write(json.dumps(response, indent=2))
