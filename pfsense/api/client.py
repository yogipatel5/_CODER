import logging
import os
from typing import Any, Dict, List, Optional

import requests

from .exceptions import raise_for_status_code

logger = logging.getLogger(__name__)


class PFSenseBaseClient:
    """Base client for interacting with pfSense API"""

    def __init__(self):
        if not os.getenv("PFSENSE_API_KEY"):
            raise ValueError("PFSENSE_API_KEY environment variable is required")
        self.base_url = os.getenv("PFSENSE_API_URL", "https://pf.ypgoc.com")
        self.headers = {"X-API-Key": os.getenv("PFSENSE_API_KEY"), "Content-Type": "application/json"}
        self.verify_ssl = os.getenv("PFSENSE_VERIFY_SSL", "true").lower() == "true"
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
        self, method: str, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Make a request to the pfSense API with error handling"""
        url = f"{self.base_url}/api/v2/{endpoint}"
        kwargs.setdefault("headers", self.headers)
        kwargs.setdefault("verify", self.verify_ssl)
        kwargs.setdefault("timeout", self.timeout)

        if params:
            kwargs["params"] = params

        try:
            logger.info(f"Making {method} request to {url}")
            response = requests.request(method, url, **kwargs)
            try:
                response_data = response.json()
            except requests.exceptions.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response: {e}")
                logger.error(f"Raw response: {response.text}")
                logger.error(f"Status code: {response.status_code}")
                raise

            # Check for API-level errors
            raise_for_status_code(response_data)

            return response_data

        except requests.exceptions.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    def apply_changes(self) -> None:
        """Apply pending changes in pfSense"""
        self._make_request("POST", "system/apply", timeout=5)


class PFSenseClient(PFSenseBaseClient):
    """Client for interacting with pfSense API"""

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
