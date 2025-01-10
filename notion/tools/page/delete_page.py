"""
Tool for deleting (archiving) Notion pages.

TODO:
- Add recursive deletion option for nested pages
- Implement deletion confirmation
- Consider soft-delete recovery period
"""

from typing import Any, Dict

from pydantic import BaseModel, Field, validator

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import PageResponse


class DeletePageInput(BaseModel):
    """Input schema for delete_page tool."""

    page_id: str = Field(..., description="ID of the page to delete")
    permanent: bool = Field(False, description="Whether to permanently delete the page (archive by default)")

    @validator("page_id")
    def validate_page_id(cls, v: str) -> str:
        """Validate page ID."""
        if not v.strip():
            raise ValueError("Page ID cannot be empty")
        return v.strip()


class DeletePageTool(NotionBaseTool):
    """Tool for deleting Notion pages."""

    name = "delete_page"
    description = "Delete (archive) a Notion page"
    args_schema = DeletePageInput

    def _run(self, page_id: str, permanent: bool = False) -> Dict[str, Any]:
        """Delete a Notion page.

        Args:
            page_id: ID of the page to delete
            permanent: Whether to permanently delete (archive by default)

        Returns:
            Dict containing success status and deleted page data
        """
        try:
            # Get page first to include title in response
            page = self.api.get_page(page_id)
            response = PageResponse.from_notion_page(page)

            if permanent:
                # Permanent deletion (if supported by API)
                self.api.delete_page(page_id)
                message = f"Permanently deleted page: {response.title}"
            else:
                # Archive the page
                self.api.update_page(page_id, {"archived": True})
                message = f"Archived page: {response.title}"

            return self._format_response(success=True, data=response.dict(), message=message)

        except Exception as e:
            return self._handle_api_error(e, "delete page")
