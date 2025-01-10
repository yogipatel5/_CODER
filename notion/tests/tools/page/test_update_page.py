"""
Tests for the UpdatePageTool.
"""

from typing import Any, Dict

import pytest

from notion.tools.page.update_page import UpdatePageInput, UpdatePageTool


class TestUpdatePageTool:
    """Test suite for UpdatePageTool."""

    def test_update_page_title(self, mocker, sample_page):
        """Test updating page title."""
        tool = UpdatePageTool()
        mocker.patch.object(tool.api, "get_page", return_value=sample_page)
        mocker.patch.object(tool.api, "update_page", return_value=sample_page)

        result = tool._run(page_id="test-page-id", title="Updated Title")
        assert result["success"] is True
        assert "title" in tool.api.update_page.call_args[0][1]["properties"]

    def test_update_page_properties(self, mocker, sample_database_page):
        """Test updating page properties."""
        tool = UpdatePageTool()
        mocker.patch.object(tool.api, "get_page", return_value=sample_database_page)
        mocker.patch.object(tool.api, "update_page", return_value=sample_database_page)

        properties = {"number": 100, "select": {"name": "Option 2"}}
        result = tool._run(page_id="test-db-page-id", properties=properties)
        assert result["success"] is True
        assert "properties" in tool.api.update_page.call_args[0][1]

    def test_update_page_archive_status(self, mocker, sample_page):
        """Test updating page archive status."""
        tool = UpdatePageTool()
        mocker.patch.object(tool.api, "get_page", return_value=sample_page)
        mocker.patch.object(tool.api, "update_page", return_value=sample_page)

        result = tool._run(page_id="test-page-id", archived=True)
        assert result["success"] is True
        assert tool.api.update_page.call_args[0][1]["archived"] is True

    def test_update_page_multiple_fields(self, mocker, sample_database_page):
        """Test updating multiple fields at once."""
        tool = UpdatePageTool()
        mocker.patch.object(tool.api, "get_page", return_value=sample_database_page)
        mocker.patch.object(tool.api, "update_page", return_value=sample_database_page)

        result = tool._run(page_id="test-db-page-id", title="New Title", properties={"number": 200}, archived=True)
        assert result["success"] is True
        update_args = tool.api.update_page.call_args[0][1]
        assert "properties" in update_args
        assert "archived" in update_args

    def test_update_page_input_validation(self):
        """Test input validation."""
        with pytest.raises(ValueError):
            UpdatePageInput(page_id="")

        with pytest.raises(ValueError):
            UpdatePageInput(page_id="test", title="")

        # Valid cases
        assert UpdatePageInput(page_id="test")
        assert UpdatePageInput(page_id="test", title="New Title")
        assert UpdatePageInput(page_id="test", properties={"key": "value"})

    def test_update_page_error_handling(self, mocker):
        """Test error handling."""
        tool = UpdatePageTool()
        mocker.patch.object(tool.api, "get_page", side_effect=Exception("API Error"))

        result = tool._run(page_id="test-page-id")
        assert result["success"] is False
        assert result["error"] is not None

    def test_update_page_not_found(self, mocker):
        """Test handling of non-existent page."""
        tool = UpdatePageTool()
        mocker.patch.object(tool.api, "get_page", side_effect=Exception("404 Not Found"))

        result = tool._run(page_id="non-existent-id")
        assert result["success"] is False
        assert "not found" in result["message"].lower()
