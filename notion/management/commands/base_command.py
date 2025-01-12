"""
Base class for Notion management commands.
"""

import os
from typing import Any, Dict, List

from crewai.tools import BaseTool
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

# Global list to store automatically registered tools
REGISTERED_NOTION_TOOLS: List[BaseTool] = []


class NotionBaseCommand(BaseCommand):
    """Base class for Notion management commands."""

    def __init__(self):
        print(f"Initializing {self.__class__.__name__}")
        super().__init__()
        token = os.getenv("NOTION_API_KEY")
        if not token:
            raise ValueError("NOTION_API_KEY environment variable is required")
        self.api = Client(auth=token)
        self._register_as_tool()

    def _register_as_tool(self) -> None:
        """Register the command's tool if it exists."""
        print(f"Checking for tool in {self.__class__.__name__}")
        if hasattr(self, "tool") and isinstance(self.tool, BaseTool):
            print(f"Found tool {self.tool.name} in {self.__class__.__name__}")
            global REGISTERED_NOTION_TOOLS
            if self.tool not in REGISTERED_NOTION_TOOLS:
                print(f"Registering tool {self.tool.name}")
                REGISTERED_NOTION_TOOLS.append(self.tool)
                print(f"Current tools: {[t.name for t in REGISTERED_NOTION_TOOLS]}")

    def get_title_from_page(self, page: Dict[str, Any]) -> str:
        """Extract title from a Notion page object."""
        # Try to get title from properties
        properties = page.get("properties", {})
        if "title" in properties:
            title_items = properties["title"].get("title", [])
            if title_items:
                return title_items[0].get("text", {}).get("content", "Untitled")

        # If no title in properties, try to get it from the page title
        if "title" in page:
            title_items = page["title"]
            if title_items:
                return title_items[0].get("text", {}).get("content", "Untitled")

        return "Untitled"

    def add_arguments(self, parser):
        """Add command-specific arguments that are common to all Notion commands."""
        parser.add_argument(
            "--format",
            choices=["json", "pretty"],
            default="json",
            help="Output format (default: json)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed progress and debug information",
        )
        parser.add_argument(
            "--raw",
            action="store_true",
            help="Return raw API response without formatting",
        )

    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement handle()")
