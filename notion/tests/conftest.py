"""
Test configuration and fixtures.
"""

import os
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest
from django.conf import settings

# Configure Django settings for tests
if not settings.configured:
    settings.configure(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        INSTALLED_APPS=["notion"],
        NOTION_API_KEY="test-token",
        NOTION_API_BASE_URL="https://api.notion.com/v1",
    )


@pytest.fixture
def mock_notion_api():
    """Mock Notion API client."""
    mock_api = MagicMock()

    # Mock successful responses
    mock_api.pages.create.return_value = {
        "id": "test-page-id",
        "object": "page",
        "created_time": "2023-01-01T00:00:00.000Z",
        "last_edited_time": "2023-01-01T00:00:00.000Z",
        "archived": False,
        "url": "https://notion.so/test-page",
        "parent": {"type": "page_id", "page_id": "parent-page-id"},
        "properties": {
            "title": {
                "id": "title",
                "type": "title",
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Test Page", "link": None},
                        "plain_text": "Test Page",
                        "href": None,
                    }
                ],
            }
        },
    }

    mock_api.pages.update.return_value = mock_api.pages.create.return_value
    mock_api.pages.delete.return_value = mock_api.pages.create.return_value
    mock_api.pages.list.return_value = {
        "object": "list",
        "results": [mock_api.pages.create.return_value],
        "next_cursor": None,
        "has_more": False,
    }

    return mock_api


@pytest.fixture
def error_responses() -> Dict[str, Dict[str, Any]]:
    """Sample error responses from Notion API."""
    return {
        "unauthorized": {"object": "error", "status": 401, "code": "unauthorized", "message": "API token is invalid."},
        "forbidden": {
            "object": "error",
            "status": 403,
            "code": "forbidden",
            "message": "Integration does not have access to this resource.",
        },
        "not_found": {"object": "error", "status": 404, "code": "not_found", "message": "Resource not found."},
        "rate_limited": {
            "object": "error",
            "status": 429,
            "code": "rate_limited",
            "message": "Rate limit exceeded.",
            "retry_after": 30,
        },
        "validation_error": {
            "object": "error",
            "status": 400,
            "code": "validation_error",
            "message": "Invalid request body.",
        },
    }


@pytest.fixture
def sample_page() -> Dict[str, Any]:
    """Sample page data from Notion API."""
    return {
        "id": "test-page-id",
        "object": "page",
        "created_time": "2023-01-01T00:00:00.000Z",
        "last_edited_time": "2023-01-01T00:00:00.000Z",
        "archived": False,
        "url": "https://notion.so/test-page",
        "parent": {"type": "page_id", "page_id": "parent-page-id"},
        "properties": {
            "title": {
                "id": "title",
                "type": "title",
                "title": [
                    {
                        "type": "text",
                        "text": {"content": "Test Page", "link": None},
                        "plain_text": "Test Page",
                        "href": None,
                    }
                ],
            },
            "Status": {"id": "status", "type": "select", "select": {"name": "In Progress", "color": "blue"}},
            "Priority": {"id": "priority", "type": "number", "number": 1},
            "Tags": {
                "id": "tags",
                "type": "multi_select",
                "multi_select": [{"name": "Feature", "color": "red"}, {"name": "Bug", "color": "yellow"}],
            },
            "Due Date": {"id": "due_date", "type": "date", "date": {"start": "2024-01-01", "end": None}},
            "Complete": {"id": "complete", "type": "checkbox", "checkbox": False},
        },
    }


@pytest.fixture
def sample_page_properties() -> Dict[str, Any]:
    """Sample page properties for testing."""
    return {
        "title": "Test Page",
        "number": 42,
        "select": {"name": "Option 1"},
        "multi_select": [{"name": "Tag 1"}, {"name": "Tag 2"}],
        "date": {"start": "2024-01-01"},
        "checkbox": True,
        "url": "https://example.com",
        "email": "test@example.com",
        "phone": "+1234567890",
    }
