import logging
import os
from typing import Any, Dict, List, Optional

import requests

from .exceptions import raise_for_status_code

logger = logging.getLogger(__name__)


class ShipperBaseClient:
    """Base client for interacting with external services"""

    def __init__(self):
        if not os.getenv("SHIPPER_API_KEY"):
            raise ValueError("SHIPPER_API_KEY environment variable is required")
        self.base_url = os.getenv("SHIPPER_API_URL", "")
        self.headers = {"X-API-Key": os.getenv("SHIPPER_API_KEY"), "Content-Type": "application/json"}
        self.verify_ssl = os.getenv("SHIPPER_VERIFY_SSL", "true").lower() == "true"
        self.timeout = 30  # Default timeout in seconds

    def _build_query_params(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[List[str]] = None,
        sort_order: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build query parameters for API requests"""
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if sort_by:
            params["sort_by"] = sort_by
        if sort_order and sort_order.upper() in ["SORT_ASC", "SORT_DESC"]:
            params["sort_order"] = sort_order.upper()
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, dict)):
                    # Handle complex filters
                    params[f"filter[{key}]"] = value
                else:
                    # Handle simple equality filters
                    params[f"filter[{key}][eq]"] = value
        return params

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict:
        """Make an HTTP request to the API"""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method,
                url,
                params=params,
                json=json,
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise


class ShipperClient(ShipperBaseClient):
    """Client for interacting with external services"""

    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a GET request to the API"""
        return self._make_request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: Dict = None) -> Dict:
        """Make a POST request to the API"""
        return self._make_request("POST", endpoint, json=json)

    def put(self, endpoint: str, json: Dict = None) -> Dict:
        """Make a PUT request to the API"""
        return self._make_request("PUT", endpoint, json=json)

    def delete(self, endpoint: str) -> Dict:
        """Make a DELETE request to the API"""
        return self._make_request("DELETE", endpoint)
