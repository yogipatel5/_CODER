"""
Tool for listing Notion pages with filtering support.

TODO [NOTION-123] [P1]: Add cursor-based pagination for large result sets
    - Implement cursor token handling ✓
    - Add pagination metadata to response ✓
    - Support both forward and backward pagination ✓

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
from notion.tools.models.page import PageResponse, PaginationMetadata


class ListPagesInput(BaseModel):
    """Input schema for list_pages tool."""

    database_id: Optional[str] = Field(None, description="Database ID to filter pages from a specific database")
    limit: int = Field(100, description="Maximum number of pages to return", ge=1, le=1000)
    archived: Optional[bool] = Field(None, description="Filter by archived status")
    cursor: Optional[str] = Field(None, description="Cursor for pagination")
    direction: str = Field("forward", description="Pagination direction (forward/backward)")

    @validator("database_id")
    def validate_database_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate database ID format if provided."""
        if v is not None and not v.strip():
            raise ValueError("Database ID cannot be empty string")
        return v

    @validator("direction")
    def validate_direction(cls, v: str) -> str:
        """Validate pagination direction."""
        if v not in ["forward", "backward"]:
            raise ValueError("Direction must be either 'forward' or 'backward'")
        return v


class ListPagesTool(NotionBaseTool):
    """Tool for listing Notion pages with filtering support."""

    name = "list_pages"
    description = "List all accessible Notion pages with optional database filter and pagination"
    args_schema = ListPagesInput

    def _run(
        self,
        database_id: Optional[str] = None,
        limit: int = 100,
        archived: Optional[bool] = None,
        cursor: Optional[str] = None,
        direction: str = "forward",
    ) -> Dict[str, Any]:
        """List Notion pages with optional filtering and pagination.

        Args:
            database_id: Optional database ID to filter pages
            limit: Maximum number of pages to return
            archived: Filter by archived status
            cursor: Cursor for pagination
            direction: Pagination direction (forward/backward)

        Returns:
            Dict containing success status, list of pages, and metadata
        """
        try:
            # Search for pages with pagination
            search_args = {
                "query": "",
                "page_size": limit,
                "start_cursor": cursor if direction == "forward" else None,
                "end_cursor": cursor if direction == "backward" else None,
            }

            response = self.api.search_pages(**search_args)
            pages = response.get("results", [])

            if not pages:
                return self._format_response(
                    success=True,
                    data={
                        "pages": [],
                        "total": 0,
                        "limit": limit,
                        "database_id": database_id,
                        "pagination": PaginationMetadata().dict(),
                    },
                    message="No pages found",
                )

            # Apply filters
            filtered_pages = self._filter_pages(pages, database_id=database_id, archived=archived)

            # Format pages and pagination metadata
            formatted_pages = [PageResponse.from_notion_page(page).dict() for page in filtered_pages]
            pagination = PaginationMetadata.from_notion_response(response)

            return self._format_response(
                success=True,
                data={
                    "pages": formatted_pages,
                    "total": len(formatted_pages),
                    "limit": limit,
                    "database_id": database_id,
                    "pagination": pagination.dict(),
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
