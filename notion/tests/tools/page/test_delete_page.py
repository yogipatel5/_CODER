"""
Tests for the DeletePageTool.
"""

import pytest
from pydantic import ValidationError

from notion.tools.page.delete_page import DeletePageTool


def test_delete_page_success(mock_notion_api):
    """Test successful page deletion."""
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
    mock_notion_api.pages.delete.return_value = sample_page

    # Create tool instance
    tool = DeletePageTool(api=mock_notion_api)

    # Run tool
    result = tool.run(page_id="test-page-id")

    # Verify success
    assert result["success"] is True
    assert result["message"] == "Page deleted successfully"
    assert result["data"]["id"] == "test-page-id"


def test_delete_page_invalid_id(mock_notion_api):
    """Test page deletion with invalid page ID."""
    # Create tool instance
    tool = DeletePageTool(api=mock_notion_api)

    # Run tool with empty page_id and expect validation error
    with pytest.raises(ValidationError):
        tool.run(page_id="")
