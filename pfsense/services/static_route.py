import logging
from typing import Dict, List

from ..api.client import PFSenseBaseClient

logger = logging.getLogger(__name__)


class StaticRouteClient(PFSenseBaseClient):
    """Client for managing pfSense static routes"""

    def get_static_routes(
        self, limit: int = 0, offset: int = 0, sort_by: List[str] = None, sort_order: str = None
    ) -> Dict:
        """
        Get all static routes from pfSense

        Args:
            limit: The number of objects to obtain at once. Set to 0 for no limit.
            offset: The starting point in the dataset to begin fetching objects.
            sort_by: The fields to sort response data by.
            sort_order: Sort order ('SORT_ASC' or 'SORT_DESC')
        """
        params = {
            "limit": limit,
            "offset": offset,
        }
        if sort_by:
            params["sort_by"] = sort_by
        if sort_order:
            params["sort_order"] = sort_order

        response = self._make_request("GET", "routing/static_routes", params=params)
        response_data = response.json()
        logger.info(f"Retrieved {len(response_data.get('data', []))} static routes")
        return response_data

    def get_static_route(self, route_id: str) -> Dict:
        """Get a specific static route from pfSense"""
        response = self._make_request("GET", f"routing/static_route/{route_id}")
        return response.json()

    def create_static_route(self, route_data: Dict) -> Dict:
        """
        Create a static route in pfSense

        Args:
            route_data: Dictionary containing route data with keys:
                - network: Network address with CIDR
                - gateway: Gateway address
                - descr: Description (optional)
                - disabled: Whether route is disabled (optional)
        """
        response = self._make_request("POST", "routing/static_route", json=route_data)
        return response.json()

    def update_static_route(self, route_id: str, route_data: Dict) -> Dict:
        """
        Update a static route in pfSense

        Args:
            route_id: ID of the route to update
            route_data: Dictionary containing route data with keys:
                - network: Network address with CIDR
                - gateway: Gateway address
                - descr: Description (optional)
                - disabled: Whether route is disabled (optional)
        """
        response = self._make_request("PUT", f"routing/static_route/{route_id}", json=route_data)
        return response.json()

    def delete_static_route(self, route_id: str) -> Dict:
        """Delete a static route from pfSense"""
        response = self._make_request("DELETE", f"routing/static_route/{route_id}")
        return response.json()
