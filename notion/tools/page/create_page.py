"""
Tool for creating Notion pages.
"""

from typing import Any, ClassVar, Dict, Type

from pydantic import BaseModel, Field, field_validator

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import PageProperties, PageResponse


class CreatePageArgs(BaseModel):
    """Page creation arguments."""

    parent_id: str = Field(..., description="Parent page or database ID")
    properties: PageProperties = Field(..., description="Page properties")

    @field_validator("parent_id")
    @classmethod
    def validate_parent_id(cls, v: str) -> str:
        """Validate parent ID."""
        if not v or not isinstance(v, str):
            raise ValueError("Parent ID must be a non-empty string")
        return v


class CreatePageTool(NotionBaseTool):
    """Tool for creating pages."""

    name: ClassVar[str] = "create_page"
    description: ClassVar[str] = "Create a new page in Notion"
    args_schema: ClassVar[Type[BaseModel]] = CreatePageArgs

    def run(self, parent_id: str, properties: PageProperties, **kwargs) -> Dict[str, Any]:
        """Create a new page."""
        try:
            # Validate arguments
            args = CreatePageArgs(parent_id=parent_id, properties=properties)

            page_data = {
                "parent": {"database_id": args.parent_id},
                "properties": args.properties.to_notion_format(),
            }

            response = self.api.pages.create(**page_data)

            # Return success response even if we can't parse the response
            if not isinstance(response, dict):
                return {
                    "success": True,
                    "message": "Page created successfully",
                    "data": {"id": str(response)},
                }

            try:
                page_response = PageResponse(**response)
                return {
                    "success": True,
                    "message": "Page created successfully",
                    "data": page_response.model_dump(),
                }
            except Exception as parse_error:
                return {
                    "success": True,
                    "message": "Page created successfully but couldn't parse response",
                    "data": response,
                    "error": str(parse_error),
                }

        except Exception as e:
            return self._handle_api_error(e, "create page")
