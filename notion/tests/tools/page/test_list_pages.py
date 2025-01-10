"""
Tests for the ListPagesTool.
"""

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from notion.tools.models.page import PageResponse
from notion.tools.page.list_pages import ListPagesArgs, ListPagesTool


class TestListPagesTool:
    """Test suite for ListPagesTool."""

    def test_list_pages_success(self, mock_notion_api, sample_page: Dict[str, Any]):
        """Test successful page listing."""
        tool = ListPagesTool()
        tool.api = mock_notion_api
        mock_notion_api.pages.list.return_value = {"results": [sample_page]}

        response = tool.run()

        assert response["success"] is True
        assert len(response["data"]) == 1
        assert response["data"][0] == PageResponse(**sample_page).model_dump()
        assert "successfully retrieved" in response["message"].lower()

    def test_list_pages_with_pagination(self, mock_notion_api, sample_page: Dict[str, Any]):
        """Test page listing with pagination."""
        tool = ListPagesTool()
        tool.api = mock_notion_api
        mock_notion_api.pages.list.return_value = {"results": [sample_page]}

        response = tool.run(cursor="test-cursor", page_size=10)

        assert response["success"] is True
        mock_notion_api.pages.list.assert_called_once_with(start_cursor="test-cursor", page_size=10)

    def test_list_pages_empty(self, mock_notion_api):
        """Test page listing with no results."""
        tool = ListPagesTool()
        tool.api = mock_notion_api
        mock_notion_api.pages.list.return_value = {"results": []}

        response = tool.run()

        assert response["success"] is True
        assert len(response["data"]) == 0
        assert "successfully retrieved" in response["message"].lower()

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
    def test_list_pages_error_handling(
        self,
        error_key: str,
        expected_message: str,
        error_responses: Dict[str, Dict[str, Any]],
        mock_notion_api,
    ):
        """Test error handling during page listing."""
        tool = ListPagesTool()
        tool.api = mock_notion_api
        error = Exception(str(error_responses[error_key]))
        mock_notion_api.pages.list.side_effect = error

        response = tool.run()

        assert response["success"] is False
        assert expected_message in response["message"].lower()
        assert response["error"] is not None
