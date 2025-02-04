"""
Example endpoint client. Use this as a template for creating endpoint-specific clients.
"""

from typing import Dict, List, Optional

from pfsense.api.client import APIClient
from pfsense.api.exceptions import APIError


class ExampleEndpoint:
    """
    Client for interacting with a specific API endpoint.
    Each endpoint class should focus on one specific service or API endpoint.
    """

    def __init__(self, client: APIClient):
        self.client = client
        self.base_path = "/api/v1/example"  # Base path for this endpoint

    def get_items(self, query: Optional[str] = None) -> List[Dict]:
        """
        Get items from the endpoint.

        Args:
            query: Optional search query

        Returns:
            List of items matching the query

        Raises:
            APIError: If the API request fails
        """
        try:
            params = {"q": query} if query else {}
            return self.client.get(f"{self.base_path}/items", params=params)
        except Exception as e:
            raise APIError(f"Failed to get items: {str(e)}")

    def create_item(self, data: Dict) -> Dict:
        """
        Create a new item.

        Args:
            data: Item data to create

        Returns:
            Created item data

        Raises:
            APIError: If the API request fails
        """
        try:
            return self.client.post(f"{self.base_path}/items", json=data)
        except Exception as e:
            raise APIError(f"Failed to create item: {str(e)}")

    def update_item(self, item_id: str, data: Dict) -> Dict:
        """
        Update an existing item.

        Args:
            item_id: ID of the item to update
            data: New item data

        Returns:
            Updated item data

        Raises:
            APIError: If the API request fails
        """
        try:
            return self.client.put(f"{self.base_path}/items/{item_id}", json=data)
        except Exception as e:
            raise APIError(f"Failed to update item: {str(e)}")

    def delete_item(self, item_id: str) -> None:
        """
        Delete an item.

        Args:
            item_id: ID of the item to delete

        Raises:
            APIError: If the API request fails
        """
        try:
            self.client.delete(f"{self.base_path}/items/{item_id}")
        except Exception as e:
            raise APIError(f"Failed to delete item: {str(e)}")
