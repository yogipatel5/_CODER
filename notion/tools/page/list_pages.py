"""
Tool for listing Notion pages.
"""

from typing import Any, ClassVar, Dict, Optional, Type

from pydantic import BaseModel, Field

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import PageResponse


class ListPagesArgs(BaseModel):
    """Page listing arguments."""

    start_cursor: Optional[str] = Field(None, description="Pagination cursor")
    page_size: Optional[int] = Field(None, description="Number of pages to return")


class ListPagesTool(NotionBaseTool):
    """Tool for listing pages."""

    name: ClassVar[str] = "list_pages"
    description: ClassVar[str] = "List pages in Notion"
    args_schema: ClassVar[Type[BaseModel]] = ListPagesArgs

    def run(self, **kwargs) -> Dict[str, Any]:
        """List pages."""
        try:
            params = {}
            if "cursor" in kwargs:
                params["start_cursor"] = kwargs["cursor"]
            if "page_size" in kwargs:
                params["page_size"] = kwargs["page_size"]

            response = self.api.pages.list(**params)
            pages = [PageResponse(**page).model_dump() for page in response.get("results", [])]

            return {
                "success": True,
                "message": f"Successfully retrieved {len(pages)} pages",
                "data": pages,
                "next_cursor": response.get("next_cursor"),
                "has_more": response.get("has_more", False),
            }
        except Exception as e:
            return self._handle_api_error(e, "list pages")
