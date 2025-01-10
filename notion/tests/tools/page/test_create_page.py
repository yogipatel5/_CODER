"""
Tests for the CreatePageTool.
"""

import pytest
from pydantic import ValidationError

from notion.tools.models.page import PageProperties
from notion.tools.page.create_page import CreatePageTool


def test_create_page_success(mock_notion_api):
    """Test successful page creation."""
    # Mock response data
    sample_page = {
        "id": "test-page-id",
        "object": "page",
        "parent": {"type": "database_id", "database_id": "test-db-id"},
        "properties": {
            "title": {
                "id": "title",
                "type": "title",
                "title": [{"type": "text", "text": {"content": "Test Page"}}],
            }
        },
    }
    mock_notion_api.pages.create.return_value = sample_page

    # Create tool instance
    tool = CreatePageTool(api=mock_notion_api)

    # Create test properties
    properties = PageProperties(title="Test Page")

    # Run tool
    result = tool.run(parent_id="test-db-id", properties=properties)

    # Verify success
    assert result["success"] is True
    assert result["message"] == "Page created successfully"
    assert result["data"]["id"] == "test-page-id"


def test_create_page_invalid_properties(mock_notion_api):
    """Test page creation with invalid properties."""
    # Create tool instance
    tool = CreatePageTool(api=mock_notion_api)

    # Create invalid properties (empty title)
    properties = PageProperties(title="")

    # Run tool and expect validation error
    with pytest.raises(ValidationError):
        tool.run(parent_id="test-db-id", properties=properties)


def test_create_page_invalid_parent_id(mock_notion_api):
    """Test page creation with invalid parent ID."""
    # Create tool instance
    tool = CreatePageTool(api=mock_notion_api)

    # Create test properties
    properties = PageProperties(title="Test Page")

    # Run tool with empty parent_id and expect validation error
    with pytest.raises(ValidationError):
        tool.run(parent_id="", properties=properties)
