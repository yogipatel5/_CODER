"""
Tool for updating existing Notion pages.

TODO [NOTION-129] [P1]: Implement optimistic locking for concurrent updates
    - Add version tracking
    - Implement conflict detection
    - Add retry mechanism

TODO [NOTION-130] [P2]: Optimize partial updates
    - Implement diff-based updates
    - Add property-level change tracking
    - Optimize API requests

TODO [NOTION-131] [P3]: Add update history tracking
    - Store update metadata
    - Track property changes
    - Implement audit logging
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import PageProperties, PageResponse


class UpdatePageInput(BaseModel):
    """Input schema for update_page tool."""

    page_id: str = Field(..., description="ID of the page to update")
    title: Optional[str] = Field(None, description="New page title")
    properties: Optional[Dict[str, Any]] = Field(None, description="Properties to update")
    archived: Optional[bool] = Field(None, description="Archive/unarchive the page")

    @validator("page_id")
    def validate_page_id(cls, v: str) -> str:
        """Validate page ID."""
        if not v.strip():
            raise ValueError("Page ID cannot be empty")
        return v.strip()

    @validator("title")
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title if provided."""
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty if provided")
        return v.strip() if v else None


class UpdatePageTool(NotionBaseTool):
    """Tool for updating Notion pages."""

    name = "update_page"
    description = "Update an existing Notion page's properties"
    args_schema = UpdatePageInput

    def _run(
        self,
        page_id: str,
        title: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        archived: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update a Notion page.

        Args:
            page_id: ID of the page to update
            title: Optional new page title
            properties: Optional properties to update
            archived: Optional archive status

        Returns:
            Dict containing success status and updated page data
        """
        try:
            # Get current page to merge properties
            current_page = self.api.get_page(page_id)
            current_properties = PageProperties.from_notion_format(current_page.get("properties", {}))

            # Create update properties
            update_props = {}
            if title:
                update_props["title"] = title
            if properties:
                update_props.update(properties)

            # Merge properties
            if update_props:
                new_properties = current_properties.merge_properties(PageProperties(**update_props))
                notion_properties = new_properties.to_notion_format()
            else:
                notion_properties = None

            # Update page
            update_data = {"properties": notion_properties} if notion_properties else {}
            if archived is not None:
                update_data["archived"] = archived

            updated_page = self.api.update_page(page_id, update_data)
            response = PageResponse.from_notion_page(updated_page)

            return self._format_response(success=True, data=response.dict(), message=f"Updated page: {response.title}")

        except Exception as e:
            return self._handle_api_error(e, "update page")
