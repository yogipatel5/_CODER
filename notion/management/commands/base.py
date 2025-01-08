"""
Base classes for Notion management commands.
"""

import logging
import os
from typing import Dict, List, Optional

import requests
from django.core.management.base import BaseCommand
from dotenv import load_dotenv

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

    def create_page(self, parent_id: str, title: str, properties: Optional[Dict] = None) -> Dict:
        """Create a new page in Notion."""
        endpoint = f"{self.base_url}/pages"
        data = {
            "parent": {"database_id": parent_id},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
        }
        if properties:
            data["properties"].update(properties)

        response = requests.post(endpoint, headers=self.headers, json=data)
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

    def get_title_from_page(self, page: Dict) -> str:
        """Extract title from a Notion page."""
        return (
            page.get("properties", {})
            .get("title", {})
            .get("title", [{}])[0]
            .get("text", {})
            .get("content", "Untitled")
        )
