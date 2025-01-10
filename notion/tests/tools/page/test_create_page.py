"""
Tests for the CreatePageTool.
"""

from typing import Any, Dict, List

import pytest

from notion.tools.models.page import BlockContent, ParentType
from notion.tools.page.create_page import CreatePageInput, CreatePageTool


class TestCreatePageTool:
    """Test suite for CreatePageTool."""

    def test_create_page_basic(self, mocker, sample_page):
        """Test creating a basic page."""
        tool = CreatePageTool()
        mocker.patch.object(tool.api, "create_page", return_value=sample_page)

        result = tool._run(title="Test Page", parent_id="parent-page-id", parent_type=ParentType.PAGE)
        assert result["success"] is True
        assert result["data"]["title"] == "Test Page"
        assert result["data"]["parent"]["type"] == "page_id"

    def test_create_page_with_properties(self, mocker, sample_database_page):
        """Test creating a page with additional properties."""
        tool = CreatePageTool()
        mocker.patch.object(tool.api, "create_page", return_value=sample_database_page)

        properties = {"number": 42, "select": {"name": "Option 1"}}
        result = tool._run(
            title="Test Database Page",
            parent_id="test-database-id",
            parent_type=ParentType.DATABASE,
            properties=properties,
        )
        assert result["success"] is True
        assert result["data"]["properties"]["number"]["number"] == 42
        assert result["data"]["properties"]["select"]["select"]["name"] == "Option 1"

    def test_create_page_with_content(self, mocker, sample_page):
        """Test creating a page with content blocks."""
        tool = CreatePageTool()
        mocker.patch.object(tool.api, "create_page", return_value=sample_page)
        mocker.patch.object(tool.api, "create_block")

        content = [BlockContent(type="paragraph", text="Test content")]
        result = tool._run(title="Test Page", parent_id="parent-page-id", parent_type=ParentType.PAGE, content=content)
        assert result["success"] is True
        tool.api.create_block.assert_called_once()

    def test_create_page_in_workspace(self, mocker, sample_page):
        """Test creating a page in workspace."""
        tool = CreatePageTool()
        mocker.patch.object(tool.api, "create_page", return_value=sample_page)

        result = tool._run(title="Test Page", parent_id="workspace", parent_type=ParentType.WORKSPACE)
        assert result["success"] is True
        assert result["data"]["parent"]["type"] == "workspace"

    def test_create_page_input_validation(self):
        """Test input validation."""
        with pytest.raises(ValueError):
            CreatePageInput(title="", parent_id="test", parent_type=ParentType.PAGE)

        with pytest.raises(ValueError):
            CreatePageInput(title="Test", parent_id="", parent_type=ParentType.PAGE)

        with pytest.raises(ValueError):
            CreatePageInput(title="Test", parent_id="test", parent_type=ParentType.WORKSPACE)

    def test_create_page_error_handling(self, mocker):
        """Test error handling."""
        tool = CreatePageTool()
        mocker.patch.object(tool.api, "create_page", side_effect=Exception("API Error"))

        result = tool._run(title="Test Page", parent_id="parent-page-id", parent_type=ParentType.PAGE)
        assert result["success"] is False
        assert result["error"] is not None
