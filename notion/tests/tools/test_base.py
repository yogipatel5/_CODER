"""
Tests for the NotionBaseTool base class.
"""

from typing import Any, Dict

import pytest

from notion.tools.base import NotionBaseTool


class TestNotionBaseTool:
    """Test suite for NotionBaseTool."""

    def test_initialize_api(self):
        """Test API client initialization."""
        tool = NotionBaseTool()
        assert tool.api is not None
        assert hasattr(tool.api, "token")
        assert hasattr(tool.api, "base_url")

    def test_format_response_success(self):
        """Test response formatting for success case."""
        tool = NotionBaseTool()
        data = {"key": "value"}
        response = tool._format_response(success=True, data=data, message="Success message")

        assert response["success"] is True
        assert response["data"] == data
        assert response["message"] == "Success message"
        assert response["error"] is None

    def test_format_response_error(self):
        """Test response formatting for error case."""
        tool = NotionBaseTool()
        response = tool._format_response(success=False, error="Error occurred", message="Error message")

        assert response["success"] is False
        assert response["data"] is None
        assert response["message"] == "Error message"
        assert response["error"] == "Error occurred"

    def test_get_title_from_page(self, sample_page: Dict[str, Any]):
        """Test title extraction from page."""
        tool = NotionBaseTool()
        title = tool._get_title_from_page(sample_page)
        assert title == "Test Page"

    def test_get_title_from_page_empty(self):
        """Test title extraction from page with no title."""
        tool = NotionBaseTool()
        title = tool._get_title_from_page({})
        assert title == "Untitled"

    def test_handle_api_error_401(self):
        """Test API error handling for 401."""
        tool = NotionBaseTool()
        error = Exception("401 Unauthorized")
        response = tool._handle_api_error(error, "test operation")

        assert response["success"] is False
        assert "authentication" in response["message"].lower()

    def test_handle_api_error_403(self):
        """Test API error handling for 403."""
        tool = NotionBaseTool()
        error = Exception("403 Forbidden")
        response = tool._handle_api_error(error, "test operation")

        assert response["success"] is False
        assert "permission" in response["message"].lower()

    def test_handle_api_error_404(self):
        """Test API error handling for 404."""
        tool = NotionBaseTool()
        error = Exception("404 Not Found")
        response = tool._handle_api_error(error, "test operation")

        assert response["success"] is False
        assert "not found" in response["message"].lower()

    def test_handle_api_error_429(self):
        """Test API error handling for 429."""
        tool = NotionBaseTool()
        error = Exception("429 Too Many Requests")
        response = tool._handle_api_error(error, "test operation")

        assert response["success"] is False
        assert "rate limit" in response["message"].lower()
