"""
Command to create a Notion page.
"""

import json
import os
from typing import List, Optional

from crewai.tools import BaseTool
from django.core.management import call_command
from dotenv import load_dotenv
from notion_client import APIResponseError

from notion.management.commands.base_command import NotionBaseCommand

load_dotenv()


class NotionCreatePageTool(BaseTool):
    """Create a new Notion page"""

    name: str = "create_notion_page"
    description: str = (
        "Create a new Notion page. Required fields: parent_id (ID of parent page), title (title of new page)"
    )

    def _run(self, parent_id: str, title: str, callbacks=None) -> str:
        """Run the notion create_page command.

        Args:
            parent_id: ID of parent page or database
            title: Title of the new page
            callbacks: Optional callback functions

        Returns:
            JSON string containing the created page details
        """
        if not parent_id or not title:
            return "Error: parent_id and title are required"

        # Capture the output using StringIO
        import sys
        from io import StringIO

        # Redirect stdout to capture the command output
        stdout_redirect = StringIO()
        sys.stdout = stdout_redirect

        try:
            call_command("notion", "create_page", parent_id, title)
            result = stdout_redirect.getvalue()
            return result
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            # Restore stdout
            sys.stdout = sys.__stdout__


class Command(NotionBaseCommand):
    help = "Create a new Notion page"

    def __new__(cls):
        instance = super().__new__(cls)
        return instance

    def __init__(self):
        super().__init__()
        self.token = os.getenv("NOTION_API_KEY")

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "parent_id",
            help="ID of the parent page or database",
        )
        parser.add_argument(
            "title",
            help="Title of the new page",
        )
        parser.add_argument(
            "--parent-type",
            default="page_id",
            choices=["page_id", "database_id", "workspace"],
            help="Type of parent (default: page_id)",
        )
        parser.add_argument(
            "--properties",
            nargs="+",
            help="Additional properties in key:value format",
        )

    def _run(
        self,
        parent_id: str,
        title: str,
        parent_type: str = "page_id",
        properties: Optional[List[str]] = None,
    ) -> str:
        """Run the command as a CrewAI tool."""
        try:
            # Convert properties list to key-value pairs
            formatted_properties = {}
            if properties:
                for prop in properties:
                    if ":" in prop:
                        key, value = prop.split(":", 1)
                        formatted_properties[key.strip()] = value.strip()

            # Prepare the parent object
            if parent_type == "workspace":
                parent = {"type": "workspace", "workspace": True}
            else:
                parent = {"type": parent_type, parent_type: parent_id}

            # Prepare properties with title
            properties = {
                "title": {"title": [{"type": "text", "text": {"content": title}}]}
            }

            # Add additional properties if provided
            for key, value in formatted_properties.items():
                properties[key] = {"rich_text": [{"text": {"content": value}}]}

            # Create the page using the correct API method
            page = self.api.pages.create(parent=parent, properties=properties)
            response = {
                "success": True,
                "message": f"Created page with ID: {page['id']}",
                "data": {
                    "id": page["id"],
                    "title": title,
                    "parent": parent,
                },
            }
            return json.dumps(response, indent=2)

        except APIResponseError as e:
            error_response = {
                "success": False,
                "message": str(e),
                "data": {
                    "title": title,
                    "parent": {
                        "type": parent_type,
                        "id": parent_id,
                    },
                },
            }
            return json.dumps(error_response, indent=2)

    def handle(self, *args, **options):
        """Handle the Django management command."""
        try:
            result = self._run(
                parent_id=options["parent_id"],
                title=options["title"],
                parent_type=options["parent_type"],
                properties=options.get("properties"),
            )
            self.stdout.write(result)
        except Exception as e:
            self.stderr.write(str(e))
