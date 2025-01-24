"""
Base class for Notion management commands.
"""

import os
from typing import Any, Dict

from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()

# Global list to store automatically registered tools


class NotionBaseCommand(BaseCommand):
    """Base class for Notion management commands."""

    def add_arguments(self, parser):
        """Add common arguments for all Notion commands."""
        parser.add_argument(
            "-v",
            "--verbosity",
            action="store",
            dest="verbosity",
            default=1,
            type=int,
            choices=[0, 1, 2, 3],
            help="Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output",
        )

    def __init__(self):
        super().__init__()
        token = os.getenv("NOTION_API_KEY")
        if not token:
            raise ValueError("NOTION_API_KEY environment variable is required")
        self.api = Client(auth=token)

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

    def handle(self, *args, **options):
        """
        The actual logic of the command. Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement handle()")
