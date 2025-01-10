"""
Tests for the CreatePageTool.
"""

from typing import Any, Dict, List

import pytest

from notion.tools.models.page import BlockContent, PageProperties, ParentType
from notion.tools.models.template import PageTemplate, TemplateVariable
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

    def test_create_page_with_template(self, mocker, sample_page):
        """Test creating a page using a template."""
        tool = CreatePageTool()
        mocker.patch.object(tool.api, "create_page", return_value=sample_page)
        mocker.patch.object(tool.api, "create_block")

        # Register a template
        template = PageTemplate(
            name="test_template",
            description="Test template",
            parent_type=ParentType.PAGE,
            properties=PageProperties(title="{title}"),
            content=[BlockContent(type="paragraph", text="Hello, {name}!")],
            variables=[
                TemplateVariable(name="title", description="Page title", required=True),
                TemplateVariable(name="name", description="Name to greet", required=True),
            ],
        )
        tool.register_template(template)

        # Create page using template
        result = tool._run(
            title="Test Page",
            parent_id="parent-page-id",
            parent_type=ParentType.PAGE,
            template="test_template",
            template_variables={"title": "Test Page", "name": "World"},
        )

        assert result["success"] is True
        assert result["data"]["title"] == "Test Page"
        tool.api.create_block.assert_called_once()

    def test_create_page_template_not_found(self, mocker):
        """Test error when template is not found."""
        tool = CreatePageTool()

        with pytest.raises(ValueError, match="Template not found: non_existent"):
            tool._run(
                title="Test Page",
                parent_id="parent-page-id",
                parent_type=ParentType.PAGE,
                template="non_existent",
                template_variables={"title": "Test"},
            )

    def test_create_page_template_parent_mismatch(self, mocker):
        """Test error when template parent type doesn't match."""
        tool = CreatePageTool()

        # Register a template for pages
        template = PageTemplate(
            name="test_template",
            description="Test template",
            parent_type=ParentType.PAGE,
            properties=PageProperties(title="{title}"),
        )
        tool.register_template(template)

        # Try to use it with database parent
        with pytest.raises(ValueError, match="Template parent type page_id does not match requested type database_id"):
            tool._run(
                title="Test Page",
                parent_id="database-id",
                parent_type=ParentType.DATABASE,
                template="test_template",
                template_variables={"title": "Test"},
            )

    def test_create_page_template_missing_variables(self, mocker):
        """Test error when required template variables are missing."""
        tool = CreatePageTool()

        # Register a template with required variables
        template = PageTemplate(
            name="test_template",
            description="Test template",
            parent_type=ParentType.PAGE,
            properties=PageProperties(title="{title}"),
            variables=[
                TemplateVariable(name="title", description="Page title", required=True),
                TemplateVariable(name="name", description="Name to greet", required=True),
            ],
        )
        tool.register_template(template)

        # Try to use it without all required variables
        with pytest.raises(ValueError, match="Missing required variables: name"):
            tool._run(
                title="Test Page",
                parent_id="parent-page-id",
                parent_type=ParentType.PAGE,
                template="test_template",
                template_variables={"title": "Test"},
            )

    def test_create_page_template_with_defaults(self, mocker, sample_page):
        """Test creating a page with template using default values."""
        tool = CreatePageTool()
        mocker.patch.object(tool.api, "create_page", return_value=sample_page)

        # Register a template with optional variables
        template = PageTemplate(
            name="test_template",
            description="Test template",
            parent_type=ParentType.PAGE,
            properties=PageProperties(title="{title}"),
            variables=[
                TemplateVariable(name="title", description="Page title", required=True),
                TemplateVariable(name="category", description="Page category", required=False, default="General"),
            ],
        )
        tool.register_template(template)

        # Create page using template with default value
        result = tool._run(
            title="Test Page",
            parent_id="parent-page-id",
            parent_type=ParentType.PAGE,
            template="test_template",
            template_variables={"title": "Test Page"},
        )

        assert result["success"] is True
        assert result["data"]["title"] == "Test Page"

    def test_create_page_template_validation(self):
        """Test template input validation."""
        with pytest.raises(ValueError, match="Template variables are required when using a template"):
            CreatePageInput(
                title="Test",
                parent_id="test",
                parent_type=ParentType.PAGE,
                template="test_template",
                template_variables=None,
            )
