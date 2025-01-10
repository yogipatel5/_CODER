"""
Tests for page operation tools.
"""

from typing import Any, Dict, List

import pytest
from pydantic import ValidationError

from notion.tools.models.page import PageProperties, PageResponse
from notion.tools.page.create_page import CreatePageTool
from notion.tools.page.delete_page import DeletePageTool
from notion.tools.page.list_pages import ListPagesTool
from notion.tools.page.update_page import UpdatePageTool


class TestPageTools:
    """Test suite for page operation tools."""

    def test_create_page_success(self, mock_notion_api, sample_page: Dict[str, Any]):
        """Test successful page creation."""
        tool = CreatePageTool()
        tool.api = mock_notion_api
        mock_notion_api.pages.create.return_value = sample_page

        response = tool.run(
            parent_id="test-parent",
            properties=PageProperties(title="Test Page"),
        )

        assert response["success"] is True
        assert response["data"] == PageResponse(**sample_page).model_dump()
        assert "created successfully" in response["message"].lower()

    def test_create_page_invalid_properties(self):
        """Test page creation with invalid properties."""
        tool = CreatePageTool()

        with pytest.raises(ValidationError) as exc_info:
            tool.run(parent_id="test-parent", properties={"invalid": "format"})

        assert "validation error" in str(exc_info.value).lower()

    def test_delete_page_success(self, mock_notion_api, sample_page: Dict[str, Any]):
        """Test successful page deletion."""
        tool = DeletePageTool()
        tool.api = mock_notion_api
        mock_notion_api.pages.delete.return_value = sample_page

        response = tool.run(page_id="test-page")

        assert response["success"] is True
        assert response["data"] == PageResponse(**sample_page).model_dump()
        assert "deleted successfully" in response["message"].lower()

    def test_list_pages_success(self, mock_notion_api, sample_page: Dict[str, Any]):
        """Test successful page listing."""
        tool = ListPagesTool()
        tool.api = mock_notion_api
        mock_notion_api.pages.list.return_value = {"results": [sample_page]}

        response = tool.run()

        assert response["success"] is True
        assert len(response["data"]) == 1
        assert response["data"][0] == PageResponse(**sample_page).model_dump()
        assert "retrieved successfully" in response["message"].lower()

    def test_update_page_success(self, mock_notion_api, sample_page: Dict[str, Any]):
        """Test successful page update."""
        tool = UpdatePageTool()
        tool.api = mock_notion_api
        mock_notion_api.pages.update.return_value = sample_page

        response = tool.run(
            page_id="test-page",
            properties=PageProperties(title="Updated Page"),
        )

        assert response["success"] is True
        assert response["data"] == PageResponse(**sample_page).model_dump()
        assert "updated successfully" in response["message"].lower()

    def test_update_page_invalid_properties(self):
        """Test page update with invalid properties."""
        tool = UpdatePageTool()

        with pytest.raises(ValidationError) as exc_info:
            tool.run(page_id="test-page", properties={"invalid": "format"})

        assert "validation error" in str(exc_info.value).lower()

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
    def test_page_tool_error_handling(
        self,
        error_key: str,
        expected_message: str,
        error_responses: Dict[str, Dict[str, Any]],
        mock_notion_api,
    ):
        """Test error handling in page tools."""
        tools = [
            CreatePageTool(),
            DeletePageTool(),
            ListPagesTool(),
            UpdatePageTool(),
        ]

        for tool in tools:
            tool.api = mock_notion_api
            error = Exception(str(error_responses[error_key]))
            mock_notion_api.pages.create.side_effect = error
            mock_notion_api.pages.delete.side_effect = error
            mock_notion_api.pages.list.side_effect = error
            mock_notion_api.pages.update.side_effect = error

            if isinstance(tool, (CreatePageTool, UpdatePageTool)):
                response = tool.run(
                    page_id="test-page" if isinstance(tool, UpdatePageTool) else None,
                    parent_id="test-parent" if isinstance(tool, CreatePageTool) else None,
                    properties=PageProperties(title="Test Page"),
                )
            else:
                response = tool.run(page_id="test-page" if isinstance(tool, DeletePageTool) else None)

            assert response["success"] is False
            assert expected_message in response["message"].lower()
            assert response["error"] is not None
