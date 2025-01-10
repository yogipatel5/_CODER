"""
Tests for the DeletePageTool.
"""

from typing import Any, Dict

import pytest

from notion.tools.page.delete_page import DeletePageInput, DeletePageTool


class TestDeletePageTool:
    """Test suite for DeletePageTool."""

    def test_delete_page_archive(self, mocker, sample_page):
        """Test archiving a page (soft delete)."""
        tool = DeletePageTool()
        mocker.patch.object(tool.api, "get_page", return_value=sample_page)
        mocker.patch.object(tool.api, "update_page", return_value=sample_page)

        result = tool._run(page_id="test-page-id")
        assert result["success"] is True
        assert tool.api.update_page.call_args[0][1]["archived"] is True

    def test_delete_page_permanent(self, mocker, sample_page):
        """Test permanently deleting a page."""
        tool = DeletePageTool()
        mocker.patch.object(tool.api, "get_page", return_value=sample_page)
        mocker.patch.object(tool.api, "delete_page")

        result = tool._run(page_id="test-page-id", permanent=True)
        assert result["success"] is True
        tool.api.delete_page.assert_called_once_with("test-page-id")

    def test_delete_database_page(self, mocker, sample_database_page):
        """Test deleting a database page."""
        tool = DeletePageTool()
        mocker.patch.object(tool.api, "get_page", return_value=sample_database_page)
        mocker.patch.object(tool.api, "update_page", return_value=sample_database_page)

        result = tool._run(page_id="test-db-page-id")
        assert result["success"] is True
        assert tool.api.update_page.call_args[0][1]["archived"] is True

    def test_delete_page_input_validation(self):
        """Test input validation."""
        with pytest.raises(ValueError):
            DeletePageInput(page_id="")

        # Valid cases
        assert DeletePageInput(page_id="test")
        assert DeletePageInput(page_id="test", permanent=True)

    def test_delete_page_error_handling(self, mocker):
        """Test error handling."""
        tool = DeletePageTool()
        mocker.patch.object(tool.api, "get_page", side_effect=Exception("API Error"))

        result = tool._run(page_id="test-page-id")
        assert result["success"] is False
        assert result["error"] is not None

    def test_delete_page_not_found(self, mocker):
        """Test handling of non-existent page."""
        tool = DeletePageTool()
        mocker.patch.object(tool.api, "get_page", side_effect=Exception("404 Not Found"))

        result = tool._run(page_id="non-existent-id")
        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_delete_page_permanent_error(self, mocker, sample_page):
        """Test error handling during permanent deletion."""
        tool = DeletePageTool()
        mocker.patch.object(tool.api, "get_page", return_value=sample_page)
        mocker.patch.object(tool.api, "delete_page", side_effect=Exception("API Error"))

        result = tool._run(page_id="test-page-id", permanent=True)
        assert result["success"] is False
        assert result["error"] is not None
