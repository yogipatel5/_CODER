"""
Tests for template tools.
"""

from typing import Any, Dict

import pytest
from pydantic import ValidationError

from notion.tools.models.template import TemplateVariable
from notion.tools.template.create_template import CreateTemplatePageTool


class TestTemplateTools:
    """Test suite for template tools."""

    def test_create_template_success(self, mock_notion_api, sample_page: Dict[str, Any]):
        """Test successful template page creation."""
        tool = CreateTemplatePageTool()
        tool.api = mock_notion_api
        mock_notion_api.pages.retrieve.return_value = sample_page
        mock_notion_api.pages.create.return_value = sample_page

        variables = [
            TemplateVariable(name="var1", value="value1", description="Variable 1"),
            TemplateVariable(name="var2", value="value2", description="Variable 2"),
        ]

        response = tool.run(
            parent_id="test-parent",
            template_id="test-template",
            variables=variables,
        )

        assert response["success"] is True
        assert "created from template successfully" in response["message"].lower()

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
    def test_template_tool_error_handling(
        self,
        error_key: str,
        expected_message: str,
        error_responses: Dict[str, Dict[str, Any]],
        mock_notion_api,
    ):
        """Test error handling in template tools."""
        tool = CreateTemplatePageTool()
        tool.api = mock_notion_api
        error = Exception(str(error_responses[error_key]))
        mock_notion_api.pages.retrieve.side_effect = error

        variables = [TemplateVariable(name="var1", value="value1", description="Variable 1")]

        response = tool.run(
            parent_id="test-parent",
            template_id="test-template",
            variables=variables,
        )

        assert response["success"] is False
        assert expected_message in response["message"].lower()
        assert response["error"] is not None
