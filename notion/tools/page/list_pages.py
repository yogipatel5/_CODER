"""
Tool for listing Notion pages with filtering support.

TODO [NOTION-123] [P1]: Add cursor-based pagination for large result sets
    - Implement cursor token handling
    - Add pagination metadata to response
    - Support both forward and backward pagination

TODO [NOTION-124] [P2]: Implement sorting options
    - Add sort by creation date
    - Add sort by last modified date
    - Support custom property sorting

TODO [NOTION-125] [P3]: Consider caching for frequently accessed pages
    - Implement cache layer
    - Add cache invalidation strategy
    - Configure cache timeouts
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from notion.tools.base import NotionBaseTool
from notion.tools.models.page import PageResponse


class ListPagesInput(BaseModel):
    """Input schema for list_pages tool."""

    database_id: Optional[str] = Field(None, description="Database ID to filter pages from a specific database")
    limit: int = Field(100, description="Maximum number of pages to return", ge=1, le=1000)
    archived: Optional[bool] = Field(None, description="Filter by archived status")

    @validator("database_id")
    def validate_database_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate database ID format if provided."""
        if v is not None and not v.strip():
            raise ValueError("Database ID cannot be empty string")
        return v


class ListPagesTool(NotionBaseTool):
    """Tool for listing Notion pages with filtering support."""

    name = "list_pages"
    description = "List all accessible Notion pages with optional database filter"
    args_schema = ListPagesInput

    def _run(
        self, database_id: Optional[str] = None, limit: int = 100, archived: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List Notion pages with optional filtering.

        Args:
            database_id: Optional database ID to filter pages
            limit: Maximum number of pages to return
            archived: Filter by archived status

        Returns:
            Dict containing success status, list of pages, and metadata
        """
        try:
            # Search for pages
            pages = self.api.search_pages("")

            if not pages:
                return self._format_response(
                    success=True,
                    data={"pages": [], "total": 0, "limit": limit, "database_id": database_id},
                    message="No pages found",
                )

            # Apply filters
            filtered_pages = self._filter_pages(pages, database_id=database_id, archived=archived)

            # Apply limit and format pages
            result_pages = filtered_pages[:limit]
            formatted_pages = [PageResponse.from_notion_page(page).dict() for page in result_pages]

            return self._format_response(
                success=True,
                data={
                    "pages": formatted_pages,
                    "total": len(formatted_pages),
                    "limit": limit,
                    "database_id": database_id,
                },
                message=f"Found {len(formatted_pages)} pages",
            )

        except Exception as e:
            return self._handle_api_error(e, "list pages")

    def _filter_pages(
        self, pages: List[Dict[str, Any]], database_id: Optional[str] = None, archived: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """Filter pages based on criteria.

        Args:
            pages: List of pages to filter
            database_id: Optional database ID filter
            archived: Optional archived status filter

        Returns:
            Filtered list of pages
        """
        filtered = pages

        # Filter by database
        if database_id:
            filtered = [page for page in filtered if page.get("parent", {}).get("database_id") == database_id]

        # Filter by archived status
        if archived is not None:
            filtered = [page for page in filtered if page.get("archived", False) == archived]

        return filtered