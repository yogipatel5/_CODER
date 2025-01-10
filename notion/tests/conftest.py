"""
Pytest configuration and shared fixtures.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from notion.tools.models.page import BlockContent, PageProperties, ParentType


@pytest.fixture
def mock_notion_api():
    """Mock Notion API client."""
    mock = MagicMock()
    mock.token = "test-token"
    mock.base_url = "https://api.notion.com/v1"
    return mock


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
def sample_block_content() -> List[BlockContent]:
    """Sample block content data."""
    return [
        BlockContent(type="paragraph", text="Test paragraph"),
        BlockContent(type="heading_1", text="Test heading"),
        BlockContent(type="bulleted_list_item", text="Test list item"),
    ]


@pytest.fixture
def sample_page_properties() -> PageProperties:
    """Sample page properties data."""
    return PageProperties(
        title="Test Page",
        rich_text=[{"text": {"content": "Test content"}}],
        number=42,
        select={"name": "Option 1"},
        checkbox=True,
        url="https://example.com",
    )


@pytest.fixture
def error_responses() -> Dict[str, Dict[str, Any]]:
    """Common API error responses."""
    return {
        "unauthorized": {
            "status": 401,
            "code": "unauthorized",
            "message": "Invalid authentication credentials",
        },
        "forbidden": {
            "status": 403,
            "code": "restricted_resource",
            "message": "User lacks access to the resource",
        },
        "not_found": {
            "status": 404,
            "code": "object_not_found",
            "message": "Resource does not exist",
        },
        "rate_limited": {
            "status": 429,
            "code": "rate_limited",
            "message": "Rate limit exceeded. Retry after: 30 seconds",
            "retry_after": 30,
        },
        "validation_error": {
            "status": 400,
            "code": "validation_error",
            "message": "Invalid request data",
        },
    }


@pytest.fixture
def mock_api_responses(sample_page, sample_database_page, error_responses):
    """Collection of mock API responses."""
    return {
        "get_page": {
            "success": sample_page,
            "database": sample_database_page,
            "error": error_responses["not_found"],
        },
        "create_page": {
            "success": sample_page,
            "error": error_responses["validation_error"],
        },
        "update_page": {
            "success": sample_page,
            "error": error_responses["forbidden"],
        },
        "delete_page": {
            "success": {"archived": True},
            "error": error_responses["unauthorized"],
        },
        "search_pages": {
            "success": {
                "results": [sample_page, sample_database_page],
                "has_more": True,
                "next_cursor": "next_cursor_value",
            },
            "empty": {
                "results": [],
                "has_more": False,
                "next_cursor": None,
            },
            "error": error_responses["rate_limited"],
        },
    }
