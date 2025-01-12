"""
Command to list Notion pages.
"""

import json
from typing import Any, Dict

from crewai.tools import BaseTool
from pydantic import BaseModel

from notion.management.commands.base_command import NotionBaseCommand


class ListPagesNotionTool(BaseTool):
    name: str = "list_notion_pages"
    description: str = (
        "List pages in Notion workspace using search. Accepts query (empty string for all pages) and limit (default 100)."
    )

    def _run(self, query: str = "", limit: int = 100) -> str:
        """This will be replaced at runtime with the command's implementation."""
        raise NotImplementedError("This method should be replaced at runtime.")


class Command(NotionBaseCommand):
    help = "List all accessible Notion pages"

    def __new__(cls):
        instance = super().__new__(cls)
        instance.tool = ListPagesNotionTool()
        return instance

    def __init__(self):
        super().__init__()
        self.tool._run = self._run

    def add_arguments(self, parser):
        super().add_arguments(parser)
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

    def _run(self, query: str = "", limit: int = 100) -> str:
        """Run the command as a CrewAI tool."""
        try:
            # Use search endpoint to find pages
            pages = self.api.search(query=query, filter={"value": "page", "property": "object"}, page_size=limit).get(
                "results", []
            )

            if not pages:
                response = {
                    "success": True,
                    "message": "No pages found",
                    "data": {"pages": [], "total": 0, "limit": limit},
                }
                return json.dumps(response, indent=2)

            # Format the response
            formatted_pages = [self.format_page_data(page) for page in pages]
            response = {
                "success": True,
                "message": f"Found {len(formatted_pages)} pages",
                "data": {
                    "pages": formatted_pages,
                    "total": len(formatted_pages),
                    "limit": limit,
                },
            }
            return json.dumps(response, indent=2)

        except Exception as e:
            error_response = {
                "success": False,
                "message": str(e),
                "data": {"pages": [], "total": 0, "limit": limit},
            }
            return json.dumps(error_response, indent=2)

    def handle(self, *args, **options):
        """Handle the Django management command."""
        try:
            result = self._run(query="", limit=options.get("limit", 100))
            self.stdout.write(result)
        except Exception as e:
            self.stderr.write(str(e))
