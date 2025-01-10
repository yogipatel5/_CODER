"""
Pydantic models for Notion page operations.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PageParent(BaseModel):
    """Parent information for a page."""

    type: str = Field(..., description="Type of parent (workspace, page_id, database_id)")
    id: str = Field(..., description="ID of the parent")

    @classmethod
    def from_notion_format(cls, parent: Dict[str, Any]) -> "PageParent":
        """Create PageParent from Notion API response format."""
        parent_type = parent.get("type", "unknown")
        parent_id = parent.get(f"{parent_type}_id", "unknown") if parent_type != "workspace" else "workspace"
        return cls(type=parent_type, id=parent_id)


class PageProperties(BaseModel):
    """Base properties for a page."""

    title: str = Field(..., description="Page title")

    @classmethod
    def from_notion_format(cls, properties: Dict[str, Any]) -> "PageProperties":
        """Create PageProperties from Notion API response format."""
        title = properties.get("title", {})
        title_text = "".join(text.get("plain_text", "") for text in title.get("title", [])) or "Untitled"
        return cls(title=title_text)

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API request format."""
        return {"title": [{"type": "text", "text": {"content": self.title}}]}


class PageResponse(BaseModel):
    """Standard page response format."""

    id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    url: Optional[str] = Field(None, description="Page URL")
    parent: PageParent = Field(..., description="Parent information")
    created_time: Optional[str] = Field(None, description="Creation timestamp")
    last_edited_time: Optional[str] = Field(None, description="Last edit timestamp")

    @classmethod
    def from_notion_page(cls, page: Dict[str, Any]) -> "PageResponse":
        """Create PageResponse from Notion page object."""
        properties = page.get("properties", {})
        title = (
            "".join(text.get("plain_text", "") for text in properties.get("title", {}).get("title", [])) or "Untitled"
        )

        return cls(
            id=page["id"],
            title=title,
            url=page.get("url"),
            parent=PageParent.from_notion_format(page["parent"]),
            created_time=page.get("created_time"),
            last_edited_time=page.get("last_edited_time"),
        )


class BlockContent(BaseModel):
    """Base model for block content."""

    type: str = Field(..., description="Block type (paragraph, heading_1, etc.)")
    content: str = Field(..., description="Block content")
    children: Optional[List["BlockContent"]] = Field(None, description="Child blocks for nested content")

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API request format."""
        block_data = {
            "type": self.type,
            self.type: {"rich_text": [{"type": "text", "text": {"content": self.content}}]},
        }

        if self.children:
            block_data["has_children"] = True
            block_data["children"] = [child.to_notion_format() for child in self.children]

        return block_data
