"""
Command to search Notion pages.
"""

import json
from typing import Any, Dict

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Search Notion pages by query"

    def add_arguments(self, parser):
        parser.add_argument("query", help="Search query")
        parser.add_argument(
            "--limit",
            type=int,
            default=100,
            help="Maximum number of pages to return (default: 100)",
        )

    def format_page_data(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Format a page for the response."""
        title = self.get_title_from_page(page)
        parent = page.get("parent", {})
        parent_type = parent.get("type", "unknown")
        parent_title = "Unknown"

        # Get the correct parent ID based on the parent type
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
        elif parent_type == "database_id":
            parent_id = parent.get("database_id", "unknown")
            parent_title = "Database"
        else:
            parent_id = "unknown"

        return {
            "id": page["id"],
            "title": title,
            "parent": {"type": parent_type, "id": parent_id, "title": parent_title},
            "url": page.get("url"),
            "created_time": page.get("created_time"),
            "last_edited_time": page.get("last_edited_time"),
        }

    def handle(self, *args, **options):
        response = {
            "success": False,
            "message": "",
            "context": "",
            "data": {"pages": [], "total": 0, "limit": options["limit"], "query": options["query"]},
            "progress": [],
        }

        try:
            # Search pages
            pages = self.api.search_pages(options["query"])

            if not pages:
                response.update(
                    {
                        "success": True,
                        "message": "No pages found matching query",
                    }
                )
                self.stdout.write(json.dumps(response, indent=2))
                return

            # Apply limit
            pages = pages[: options["limit"]]

            # Format the response
            formatted_pages = [self.format_page_data(page) for page in pages]
            response.update(
                {
                    "success": True,
                    "message": f"Found {len(pages)} pages matching query",
                    "data": {
                        "pages": formatted_pages,
                        "total": len(pages),
                        "limit": options["limit"],
                        "query": options["query"],
                    },
                }
            )

        except Exception as e:
            response.update({"message": "Error searching pages", "error": str(e)})

        self.stdout.write(json.dumps(response, indent=2))