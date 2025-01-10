"""
Tool for updating Notion pages.
"""

from typing import Any, ClassVar, Dict, Type

from pydantic import BaseModel, Field, field_validator

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import PageProperties, PageResponse


class UpdatePageArgs(BaseModel):
    """Page update arguments."""

    page_id: str = Field(..., description="Page ID to update")
    properties: PageProperties = Field(..., description="Updated page properties")

    @field_validator("page_id")
    @classmethod
    def validate_page_id(cls, v: str) -> str:
        """Validate page ID."""
        if not v or not isinstance(v, str):
            raise ValueError("Page ID must be a non-empty string")
        return v


class UpdatePageTool(NotionBaseTool):
    """Tool for updating pages."""

    name: ClassVar[str] = "update_page"
    description: ClassVar[str] = "Update a page in Notion"
    args_schema: ClassVar[Type[BaseModel]] = UpdatePageArgs

    def run(self, page_id: str, properties: PageProperties, **kwargs) -> Dict[str, Any]:
        """Update an existing page."""
        try:
            # Validate arguments
            args = UpdatePageArgs(page_id=page_id, properties=properties)

            page_data = {
                "page_id": args.page_id,
                "properties": args.properties.to_notion_format(),
            }

            response = self.api.pages.update(**page_data)

            # Return success response even if we can't parse the response
            if not isinstance(response, dict):
                return {
                    "success": True,
                    "message": "Page updated successfully",
                    "data": {"id": str(response)},
                }

            try:
                page_response = PageResponse(**response)
                return {
                    "success": True,
                    "message": "Page updated successfully",
                    "data": page_response.model_dump(),
                }
            except Exception as parse_error:
                return {
                    "success": True,
                    "message": "Page updated successfully but couldn't parse response",
                    "data": response,
                    "error": str(parse_error),
                }

        except Exception as e:
            return self._handle_api_error(e, "update page")
