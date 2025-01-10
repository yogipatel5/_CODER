"""
Tests for the NotionBaseTool base class.
"""

from typing import Any, Dict

import pytest

from notion.tests.tools.utils.test_tools import TestNotionTool
from notion.tools.base import NotionBaseTool


class TestNotionBaseTool:
    """Test suite for NotionBaseTool."""

    def test_initialize_api(self, mock_notion_api):
        """Test API client initialization."""
        tool = TestNotionTool()
        tool.api = mock_notion_api

        assert tool.api is not None
        assert tool.api.token == "test-token"
        assert tool.api.base_url == "https://api.notion.com/v1"

    def test_format_response_success(self):
        """Test response formatting for success case."""
        tool = TestNotionTool()
        data = {"key": "value"}
        response = tool._format_response(success=True, data=data, message="Success message")

        assert response["success"] is True
        assert response["data"] == data
        assert response["message"] == "Success message"
        assert response["error"] is None

    def test_format_response_error(self):
        """Test response formatting for error case."""
        tool = TestNotionTool()
        response = tool._format_response(success=False, error="Error occurred", message="Error message")

        assert response["success"] is False
        assert response["data"] is None
        assert response["message"] == "Error message"
        assert response["error"] == "Error occurred"

    def test_get_title_from_page(self, sample_page: Dict[str, Any]):
        """Test title extraction from page."""
        tool = TestNotionTool()
        title = tool._get_title_from_page(sample_page)
        assert title == "Test Page"

    def test_get_title_from_page_empty(self):
        """Test title extraction from page with no title."""
        tool = TestNotionTool()
        title = tool._get_title_from_page({})
        assert title == "Untitled"

    @pytest.mark.parametrize(
        "error_key,expected_message",
        [
            ("unauthorized", "authentication"),
            ("forbidden", "permission"),
            ("not_found", "not found"),
            ("rate_limited", "rate limit"),
            ("validation_error", "validation"),
        ],
    )
    def test_handle_api_errors(self, error_key: str, expected_message: str, error_responses: Dict[str, Dict[str, Any]]):
        """Test API error handling for different error types."""
        tool = TestNotionTool()
        error = Exception(str(error_responses[error_key]))
        response = tool._handle_api_error(error, "test operation")

        assert response["success"] is False
        assert expected_message in response["message"].lower()
        assert response["error"] is not None

    def test_handle_unknown_error(self):
        """Test handling of unknown error types."""
        tool = TestNotionTool()
        error = Exception("Unknown error")
        response = tool._handle_api_error(error, "test operation")

        assert response["success"] is False
        assert "failed" in response["message"].lower()
        assert response["error"] == "Unknown error"
