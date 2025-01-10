"""
Tool for creating new Notion pages.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import BlockContent, PageParent, PageProperties, PageResponse, ParentType


class CreatePageInput(BaseModel):
    """Input schema for create_page tool."""

    title: str = Field(..., description="Page title")
    parent_id: str = Field(..., description="ID of parent (workspace/page/database)")
    parent_type: ParentType = Field(..., description="Type of parent")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional page properties (for database pages)")
    content: Optional[List[BlockContent]] = Field(None, description="Page content blocks")

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


class CreatePageTool(NotionBaseTool):
    """Tool for creating new Notion pages."""

    name = "create_page"
    description = "Create a new Notion page with specified parent and content"
    args_schema = CreatePageInput

    def _run(
        self,
        title: str,
        parent_id: str,
        parent_type: ParentType,
        properties: Optional[Dict[str, Any]] = None,
        content: Optional[List[BlockContent]] = None,
    ) -> Dict[str, Any]:
        """Create a new Notion page.

        Args:
            title: Page title
            parent_id: ID of parent (workspace/page/database)
            parent_type: Type of parent
            properties: Additional page properties
            content: Page content blocks

        Returns:
            Dict containing success status and created page data
        """
        try:
            # Create base properties
            page_properties = PageProperties(title=title)
            if properties:
                page_properties = page_properties.merge_properties(PageProperties(**properties))

            # Create page
            page = self.api.create_page(
                parent_id=parent_id, title=title, properties=page_properties.to_notion_format(), parent_type=parent_type
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
