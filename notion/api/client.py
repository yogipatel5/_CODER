"""Notion API client implementation."""
from typing import Dict, List

from django.conf import settings
from notion_client import Client


class NotionClient:
    """Client for interacting with the Notion API."""

    def __init__(self):
        """Initialize the Notion client."""
        self.client = Client(auth=settings.NOTION_API_KEY)

    def get_page(self, page_id: str) -> Dict:
        """Retrieve a page from Notion.

        Args:
            page_id: The ID of the page to retrieve

        Returns:
            Dict containing the page data
        """
        return self.client.pages.retrieve(page_id)

    def search_pages(self, query: str) -> List[Dict]:
        """Search for pages in Notion.

        Args:
            query: The search query string

        Returns:
            List of dictionaries containing matching pages
        """
        response = self.client.search(query=query)
        return response.get("results", [])

    def update_page(self, page_id: str, properties: Dict) -> Dict:
        """Update a page in Notion.

        Args:
            page_id: The ID of the page to update
            properties: Dictionary of properties to update

        Returns:
            Dict containing the updated page data
        """
        return self.client.pages.update(page_id=page_id, properties=properties)

    def create_page(self, parent: Dict, properties: Dict) -> Dict:
        """Create a new page in Notion.

        Args:
            parent: Dictionary specifying the parent (workspace or page)
            properties: Dictionary of page properties

        Returns:
            Dict containing the created page data
        """
        return self.client.pages.create(parent=parent, properties=properties)

    def get_block_children(self, block_id: str) -> List[Dict]:
        """Get children blocks of a block.

        Args:
            block_id: The ID of the block

        Returns:
            List of dictionaries containing child blocks
        """
        response = self.client.blocks.children.list(block_id=block_id)
        return response.get("results", [])

    def append_block_children(self, block_id: str, children: List[Dict]) -> Dict:
        """Append children blocks to a block.

        Args:
            block_id: The ID of the parent block
            children: List of block objects to append

        Returns:
            Dict containing the response data
        """
        return self.client.blocks.children.append(block_id=block_id, children=children)


if __name__ == "__main__":
    client = NotionClient()
    page = client.get_page("17d9167955c8802bbb62f646e9e23318")
