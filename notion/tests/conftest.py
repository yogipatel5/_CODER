"""
Pytest configuration and shared fixtures.
"""

from typing import Any, Dict

import pytest


@pytest.fixture
def sample_page() -> Dict[str, Any]:
    """Sample Notion page data."""
    return {
        "id": "test-page-id",
        "parent": {"type": "page_id", "page_id": "parent-page-id"},
        "properties": {"title": {"title": [{"text": {"content": "Test Page"}}]}},
        "url": "https://notion.so/test-page",
        "created_time": "2024-01-01T00:00:00Z",
        "last_edited_time": "2024-01-01T00:00:00Z",
        "archived": False,
    }


@pytest.fixture
def sample_database_page() -> Dict[str, Any]:
    """Sample Notion database page data."""
    return {
        "id": "test-db-page-id",
        "parent": {"type": "database_id", "database_id": "test-database-id"},
        "properties": {
            "title": {"title": [{"text": {"content": "Test Database Page"}}]},
            "number": {"type": "number", "number": 42},
            "select": {"type": "select", "select": {"name": "Option 1"}},
        },
        "url": "https://notion.so/test-db-page",
        "created_time": "2024-01-01T00:00:00Z",
        "last_edited_time": "2024-01-01T00:00:00Z",
        "archived": False,
    }


@pytest.fixture
def error_responses() -> Dict[str, Dict[str, Any]]:
    """Common API error responses."""
    return {
        "unauthorized": {"status": 401, "message": "Invalid authentication credentials"},
        "forbidden": {"status": 403, "message": "User lacks access to the resource"},
        "not_found": {"status": 404, "message": "Resource does not exist"},
        "rate_limited": {"status": 429, "message": "Rate limit exceeded"},
    }
