"""
Tests for the UpdatePageTool.
"""

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from notion.tools.models.page import PageProperties, PageResponse
from notion.tools.page.update_page import UpdatePageArgs, UpdatePageTool


class TestUpdatePageTool:
    """Test suite for UpdatePageTool."""

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
    def test_update_page_error_handling(
        self,
        error_key: str,
        expected_message: str,
        error_responses: Dict[str, Dict[str, Any]],
        mock_notion_api,
    ):
        """Test error handling during page update."""
        tool = UpdatePageTool()
        tool.api = mock_notion_api
        error = Exception(str(error_responses[error_key]))
        mock_notion_api.pages.update.side_effect = error

        response = tool.run(
            page_id="test-page",
            properties=PageProperties(title="Updated Page"),
        )

        assert response["success"] is False
        assert expected_message in response["message"].lower()
        assert response["error"] is not None
