"""
Pydantic models for Notion page operations.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ParentType(str, Enum):
    """Valid parent types for Notion pages."""

    WORKSPACE = "workspace"
    PAGE = "page_id"
    DATABASE = "database_id"


class BlockType(str, Enum):
    """Supported Notion block types."""

    PARAGRAPH = "paragraph"
    HEADING_1 = "heading_1"
    HEADING_2 = "heading_2"
    HEADING_3 = "heading_3"
    BULLETED_LIST = "bulleted_list_item"
    NUMBERED_LIST = "numbered_list_item"
    TO_DO = "to_do"
    TOGGLE = "toggle"
    CODE = "code"
    QUOTE = "quote"
    CALLOUT = "callout"
    DIVIDER = "divider"


class PropertyType(str, Enum):
    """Supported Notion property types."""

    TITLE = "title"
    RICH_TEXT = "rich_text"
    NUMBER = "number"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    DATE = "date"
    CHECKBOX = "checkbox"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"


class PageParent(BaseModel):
    """Parent information for a page."""

    type: ParentType = Field(..., description="Type of parent")
    id: str = Field(..., description="ID of the parent")

    @validator("type")
    def validate_parent_type(cls, v: str) -> str:
        """Validate parent type is supported."""
        if v not in ParentType.__members__.values():
            raise ValueError(f"Unsupported parent type: {v}")
        return v

    @classmethod
    def from_notion_format(cls, parent: Dict[str, Any]) -> "PageParent":
        """Create PageParent from Notion API response format."""
        try:
            parent_type = parent.get("type")
            if not parent_type:
                raise ValueError("Missing parent type")

            if parent_type not in ParentType.__members__.values():
                raise ValueError(f"Invalid parent type: {parent_type}")

            parent_id = parent.get(f"{parent_type}_id") if parent_type != ParentType.WORKSPACE else ParentType.WORKSPACE

            if not parent_id:
                raise ValueError("Missing parent ID")

            return cls(type=parent_type, id=parent_id)
        except Exception as e:
            raise ValueError(f"Invalid parent data: {str(e)}")


class PageProperties(BaseModel):
    """Base properties for a page."""

    title: str = Field(..., description="Page title")
    rich_text: Optional[List[Dict[str, Any]]] = Field(None, description="Rich text content")
    number: Optional[float] = Field(None, description="Number value")
    select: Optional[Dict[str, str]] = Field(None, description="Select option")
    multi_select: Optional[List[Dict[str, str]]] = Field(None, description="Multi-select options")
    date: Optional[Dict[str, str]] = Field(None, description="Date value")
    checkbox: Optional[bool] = Field(None, description="Checkbox value")
    url: Optional[str] = Field(None, description="URL value")
    email: Optional[str] = Field(None, description="Email value")
    phone: Optional[str] = Field(None, description="Phone number")

    @validator("*", pre=True)
    def validate_property_types(cls, v: Any, field: Field) -> Any:
        """Validate property types match expected formats."""
        if v is None:
            return v

        if field.name in PropertyType.__members__.values():
            if not isinstance(v, field.type_):
                raise ValueError(f"Invalid type for {field.name}: expected {field.type_}, got {type(v)}")
        return v

    @classmethod
    def from_notion_format(cls, properties: Dict[str, Any]) -> "PageProperties":
        """Create PageProperties from Notion API response format."""
        try:
            formatted_props = {}

            for key, value in properties.items():
                prop_type = value.get("type")
                if prop_type not in PropertyType.__members__.values():
                    continue

                if prop_type == PropertyType.TITLE:
                    formatted_props["title"] = (
                        "".join(text.get("plain_text", "") for text in value.get("title", [])) or "Untitled"
                    )
                else:
                    formatted_props[prop_type] = value.get(prop_type)

            return cls(**formatted_props)
        except Exception as e:
            raise ValueError(f"Invalid properties data: {str(e)}")

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API request format."""
        notion_props = {}

        for field, value in self.dict(exclude_none=True).items():
            if field == "title":
                notion_props["title"] = {"title": [{"type": "text", "text": {"content": value}}]}
            elif field in PropertyType.__members__.values():
                notion_props[field] = {field: value}

        return notion_props

    def merge_properties(self, other: "PageProperties") -> "PageProperties":
        """Merge another PageProperties instance with this one."""
        merged_data = self.dict(exclude_none=True)
        other_data = other.dict(exclude_none=True)

        for key, value in other_data.items():
            if value is not None:
                merged_data[key] = value

        return PageProperties(**merged_data)


class PageResponse(BaseModel):
    """Standard page response format."""

    id: str = Field(..., description="Page ID")
    title: str = Field(..., description="Page title")
    url: Optional[str] = Field(None, description="Page URL")
    parent: PageParent = Field(..., description="Parent information")
    properties: PageProperties = Field(..., description="Page properties")
    created_time: Optional[str] = Field(None, description="Creation timestamp")
    last_edited_time: Optional[str] = Field(None, description="Last edit timestamp")
    archived: bool = Field(False, description="Whether the page is archived")

    @validator("id")
    def validate_required_fields(cls, v: str) -> str:
        """Validate required Notion fields."""
        if not v or not isinstance(v, str):
            raise ValueError("Invalid or missing page ID")
        return v

    @classmethod
    def from_notion_page(cls, page: Dict[str, Any]) -> "PageResponse":
        """Create PageResponse from Notion page object."""
        try:
            if not page.get("id"):
                raise ValueError("Missing required field: id")

            properties = page.get("properties", {})
            if not properties:
                raise ValueError("Missing required field: properties")

            return cls(
                id=page["id"],
                title=PageProperties.from_notion_format(properties).title,
                url=page.get("url"),
                parent=PageParent.from_notion_format(page["parent"]),
                properties=PageProperties.from_notion_format(properties),
                created_time=page.get("created_time"),
                last_edited_time=page.get("last_edited_time"),
                archived=page.get("archived", False),
            )
        except Exception as e:
            raise ValueError(f"Invalid page data: {str(e)}")

    def get_property(self, name: str) -> Any:
        """Get a property value by name."""
        return getattr(self.properties, name, None)

    def is_accessible(self) -> bool:
        """Check if the page is accessible (not archived)."""
        return not self.archived


class RichText(BaseModel):
    """Rich text formatting options."""

    content: str = Field(..., description="Text content")
    bold: Optional[bool] = Field(None, description="Bold formatting")
    italic: Optional[bool] = Field(None, description="Italic formatting")
    strikethrough: Optional[bool] = Field(None, description="Strikethrough formatting")
    underline: Optional[bool] = Field(None, description="Underline formatting")
    code: Optional[bool] = Field(None, description="Code formatting")
    color: Optional[str] = Field(None, description="Text color")

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API rich text format."""
        text_format = {"type": "text", "text": {"content": self.content}}

        annotations = {}
        for field in ["bold", "italic", "strikethrough", "underline", "code", "color"]:
            value = getattr(self, field)
            if value is not None:
                annotations[field] = value

        if annotations:
            text_format["annotations"] = annotations

        return text_format


class BlockContent(BaseModel):
    """Base model for block content."""

    type: BlockType = Field(..., description="Block type")
    content: str = Field(..., description="Block content")
    children: Optional[List["BlockContent"]] = Field(None, description="Child blocks")
    rich_text: Optional[List[RichText]] = Field(None, description="Rich text formatting")

    @validator("type")
    def validate_block_type(cls, v: str) -> str:
        """Validate block type is supported."""
        if v not in BlockType.__members__.values():
            raise ValueError(f"Unsupported block type: {v}")
        return v

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API request format."""
        block_data = {
            "type": self.type,
            self.type: {
                "rich_text": [text.to_notion_format() for text in (self.rich_text or [RichText(content=self.content)])]
            },
        }

        if self.children:
            block_data["has_children"] = True
            block_data["children"] = [child.to_notion_format() for child in self.children]

        return block_data

    @classmethod
    def create_batch(cls, blocks: List["BlockContent"]) -> List[Dict[str, Any]]:
        """Create multiple blocks in Notion format."""
        return [block.to_notion_format() for block in blocks]


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""

    has_more: bool = Field(False, description="Whether there are more results available")
    next_cursor: Optional[str] = Field(None, description="Cursor for the next page of results")
    prev_cursor: Optional[str] = Field(None, description="Cursor for the previous page of results")
    total_results: Optional[int] = Field(None, description="Total number of results if known")

    @classmethod
    def from_notion_response(cls, response: Dict[str, Any]) -> "PaginationMetadata":
        """Create pagination metadata from Notion API response."""
        return cls(
            has_more=response.get("has_more", False),
            next_cursor=response.get("next_cursor"),
            total_results=response.get("total_results"),
        )
