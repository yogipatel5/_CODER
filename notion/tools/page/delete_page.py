"""
Tool for deleting Notion pages.
"""

from typing import Any, ClassVar, Dict, Type

from pydantic import BaseModel, Field, field_validator

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import PageResponse


class DeletePageArgs(BaseModel):
    """Page deletion arguments."""

    page_id: str = Field(..., description="Page ID to delete")

    @field_validator("page_id")
    @classmethod
    def validate_page_id(cls, v: str) -> str:
        """Validate page ID."""
        if not v or not isinstance(v, str):
            raise ValueError("Page ID must be a non-empty string")
        return v


class DeletePageTool(NotionBaseTool):
    """Tool for deleting pages."""

    name: ClassVar[str] = "delete_page"
    description: ClassVar[str] = "Delete a page from Notion"
    args_schema: ClassVar[Type[BaseModel]] = DeletePageArgs

    def run(self, page_id: str, **kwargs) -> Dict[str, Any]:
        """Delete a page."""
        try:
            # Validate arguments
            args = DeletePageArgs(page_id=page_id)

            response = self.api.pages.delete(page_id=args.page_id)

            # Return success response even if we can't parse the response
            if not isinstance(response, dict):
                return {
                    "success": True,
                    "message": "Page deleted successfully",
                    "data": {"id": str(response)},
                }

            try:
                page_response = PageResponse(**response)
                return {
                    "success": True,
                    "message": "Page deleted successfully",
                    "data": page_response.model_dump(),
                }
            except Exception as parse_error:
                return {
                    "success": True,
                    "message": "Page deleted successfully but couldn't parse response",
                    "data": response,
                    "error": str(parse_error),
                }

        except Exception as e:
            return self._handle_api_error(e, "delete page")
