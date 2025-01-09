"""
Base classes for Notion management commands.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import requests
from crewai.tools import BaseTool
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()
logger = logging.getLogger(__name__)


class NotionAPI:
    """Notion API client."""

    def __init__(self):
        self.token = os.getenv("NOTION_API_KEY")
        if not self.token:
            raise ValueError("NOTION_API_KEY environment variable is required")

        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

    def list_databases(self) -> List[Dict]:
        """List all accessible Notion databases."""
        endpoint = f"{self.base_url}/search"
        data = {"filter": {"property": "object", "value": "database"}}
        response = requests.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json().get("results", [])

    def search_pages(self, query: str) -> List[Dict]:
        """Search Notion pages with the given query."""
        endpoint = f"{self.base_url}/search"
        data = {"query": query, "filter": {"property": "object", "value": "page"}}
        response = requests.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json().get("results", [])

    def create_page(
        self, parent_id: str, title: str, properties: Optional[Dict] = None, parent_type: str = "page_id"
    ) -> Dict:
        """Create a new page in Notion.

        Args:
            parent_id: ID of the parent (page or database)
            title: Title of the new page
            properties: Additional properties for the page
            parent_type: Type of parent ("page_id", "database_id", or "workspace")
        """
        endpoint = f"{self.base_url}/pages"

        # Set up the parent object based on type
        if parent_type == "workspace":
            parent = {"workspace": True}
        else:
            parent = {parent_type: parent_id}

        # Set up the properties
        if parent_type == "database_id":
            # For database parents, title is a property
            page_properties = {"title": {"title": [{"text": {"content": title}}]}}
            if properties:
                page_properties.update(properties)
        else:
            # For page/workspace parents, use rich_text for content
            page_properties = {}
            if properties:
                page_properties.update(properties)

        data = {
            "parent": parent,
            "properties": page_properties,
        }

        # For page/workspace parents, add content as blocks
        if parent_type != "database_id":
            data["children"] = [
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {"rich_text": [{"type": "text", "text": {"content": title}}]},
                }
            ]

        response = requests.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def get_page(self, page_id: str) -> Dict:
        """Get a specific page by ID."""
        endpoint = f"{self.base_url}/pages/{page_id}"
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_block_children(self, block_id: str, page_size: int = 100) -> List[Dict]:
        """Get all child blocks of a block."""
        endpoint = f"{self.base_url}/blocks/{block_id}/children"
        params = {"page_size": page_size}
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json().get("results", [])

    def update_page(self, page_id: str, properties: Dict) -> Dict:
        """Update a page's properties."""
        endpoint = f"{self.base_url}/pages/{page_id}"
        data = {"properties": properties}
        response = requests.patch(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def delete_page(self, page_id: str) -> Dict:
        """Archive/delete a page."""
        endpoint = f"{self.base_url}/pages/{page_id}"
        data = {"archived": True}
        response = requests.patch(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def create_block(self, page_id: str, blocks: List[Dict]) -> Dict:
        """Create new blocks in a page."""
        endpoint = f"{self.base_url}/blocks/{page_id}/children"
        data = {"children": blocks}
        response = requests.patch(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def update_block(self, block_id: str, block_data: Dict) -> Dict:
        """Update a specific block."""
        endpoint = f"{self.base_url}/blocks/{block_id}"
        response = requests.patch(endpoint, headers=self.headers, json=block_data)
        response.raise_for_status()
        return response.json()

    def delete_block(self, block_id: str) -> Dict:
        """Delete a specific block."""
        endpoint = f"{self.base_url}/blocks/{block_id}"
        response = requests.delete(endpoint, headers=self.headers)
        response.raise_for_status()
        return response.json()


class NotionBaseCommand(BaseCommand):
    """Base class for Notion management commands."""

    def __init__(self):
        super().__init__()
        self.api = NotionAPI()

    def add_arguments(self, parser):
        """Add command-specific arguments."""
        pass  # To be implemented by subclasses

    def get_title_from_page(self, page: Dict[str, Any]) -> str:
        """Extract the title from a page object."""
        title = page.get("properties", {}).get("title", {})
        if not title:
            return "Untitled"

        title_parts = []
        for text in title.get("title", []):
            title_parts.append(text.get("plain_text", ""))

        return "".join(title_parts) or "Untitled"

    def get_text_content(self, rich_text: List[Dict[str, Any]]) -> str:
        """Extract plain text content from rich text array."""
        if not rich_text:
            return ""
        return "".join(text.get("plain_text", "") for text in rich_text)
