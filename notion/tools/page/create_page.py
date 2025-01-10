"""
Tool for creating new Notion pages.

TODO [NOTION-126] [P1]: Add template support for common page structures
    - Define template schema
    - Implement template loading
    - Add template validation

TODO [NOTION-127] [P2]: Implement batch creation method
    - Support multiple page creation
    - Add transaction handling
    - Implement rollback on failure

TODO [NOTION-128] [P3]: Add duplicate detection mechanism
    - Implement title similarity check
    - Add content hash comparison
    - Configure duplicate thresholds
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import BlockContent, PageParent, PageProperties, PageResponse, ParentType
from notion.tools.models.template import PageTemplate


class CreatePageInput(BaseModel):
    """Input schema for create_page tool."""

    title: str = Field(..., description="Page title")
    parent_id: str = Field(..., description="ID of parent (workspace/page/database)")
    parent_type: ParentType = Field(..., description="Type of parent")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional page properties (for database pages)")
    content: Optional[List[BlockContent]] = Field(None, description="Page content blocks")
    template: Optional[str] = Field(None, description="Template name to use")
    template_variables: Optional[Dict[str, Any]] = Field(None, description="Variables for template rendering")

    @validator("title")
    def validate_title(cls, v: str) -> str:
        """Validate page title."""
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @validator("parent_id")
    def validate_parent_id(cls, v: str, values: Dict[str, Any]) -> str:
        """Validate parent ID based on type."""
        if not v.strip():
            raise ValueError("Parent ID cannot be empty")

        parent_type = values.get("parent_type")
        if parent_type == ParentType.WORKSPACE and v != "workspace":
            raise ValueError("Parent ID must be 'workspace' for workspace parent type")

        return v.strip()

    @validator("template_variables")
    def validate_template_variables(
        cls, v: Optional[Dict[str, Any]], values: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Validate template variables are provided if template is specified."""
        if values.get("template") and not v:
            raise ValueError("Template variables are required when using a template")
        return v


class CreatePageTool(NotionBaseTool):
    """Tool for creating new Notion pages."""

    name = "create_page"
    description = "Create a new Notion page with specified parent and content"
    args_schema = CreatePageInput

    def __init__(self):
        """Initialize the tool with templates."""
        super().__init__()
        self.templates: Dict[str, PageTemplate] = {}

    def register_template(self, template: PageTemplate) -> None:
        """Register a page template.

        Args:
            template: Template to register
        """
        self.templates[template.name] = template

    def _run(
        self,
        title: str,
        parent_id: str,
        parent_type: ParentType,
        properties: Optional[Dict[str, Any]] = None,
        content: Optional[List[BlockContent]] = None,
        template: Optional[str] = None,
        template_variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new Notion page.

        Args:
            title: Page title
            parent_id: ID of parent (workspace/page/database)
            parent_type: Type of parent
            properties: Additional page properties
            content: Page content blocks
            template: Template name to use
            template_variables: Variables for template rendering

        Returns:
            Dict containing success status and created page data
        """
        try:
            # Handle template if specified
            if template:
                if template not in self.templates:
                    raise ValueError(f"Template not found: {template}")

                template_obj = self.templates[template]
                if template_obj.parent_type != parent_type:
                    raise ValueError(
                        f"Template parent type {template_obj.parent_type} does not match requested type {parent_type}"
                    )

                rendered = template_obj.render(template_variables or {})
                properties = rendered["properties"]
                content = rendered.get("content")

            # Create base properties
            page_properties = PageProperties(title=title)
            if properties:
                page_properties = page_properties.merge_properties(PageProperties(**properties))

            # Create page
            page = self.api.create_page(
                parent_id=parent_id,
                title=title,
                properties=page_properties.to_notion_format(),
                parent_type=parent_type,
            )

            # Add content blocks if provided
            if content and parent_type != ParentType.DATABASE:
                blocks = BlockContent.create_batch(content)
                self.api.create_block(page["id"], blocks)

            # Format response
            response = PageResponse.from_notion_page(page)

            return self._format_response(success=True, data=response.dict(), message=f"Created page: {response.title}")

        except Exception as e:
            return self._handle_api_error(e, "create page")
