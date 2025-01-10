"""
Pydantic models for Notion page operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, ValidationError, ValidationInfo, field_validator, model_validator

from notion.tools.errors import NotionError


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


class NotionError(Exception):
    """Custom error class for Notion-related errors."""

    def __init__(self, message: str, error_type: str, status_code: int):
        self.error_type = error_type
        self.status_code = status_code
        super().__init__(message)

    @classmethod
    def from_api_error(cls, error: Exception, operation: str) -> "NotionError":
        """Create NotionError from API error response."""
        error_str = str(error).lower()

        if "unauthorized" in error_str or "authentication" in error_str:
            return cls(message=f"Authentication failed during {operation}", error_type="unauthorized", status_code=401)
        elif "forbidden" in error_str or "permission" in error_str:
            return cls(message=f"Permission denied during {operation}", error_type="forbidden", status_code=403)
        elif "not found" in error_str or "does not exist" in error_str:
            return cls(message=f"Resource not found during {operation}", error_type="not_found", status_code=404)
        elif "rate limit" in error_str or "too many requests" in error_str:
            return cls(message=f"Rate limit exceeded during {operation}", error_type="rate_limited", status_code=429)
        elif "validation" in error_str or "invalid" in error_str:
            return cls(
                message=f"Validation error during {operation}: {str(error)}", error_type="validation", status_code=400
            )
        else:
            return cls(message=f"Operation failed: {str(error)}", error_type="unknown", status_code=500)


class PageParent(BaseModel):
    """Parent information for a page."""

    type: ParentType = Field(..., description="Type of parent")
    id: str = Field(..., description="ID of the parent", min_length=1)

    model_config = ConfigDict(strict=True, populate_by_name=True, validate_assignment=True)

    @field_validator("type", mode="before")
    @classmethod
    def validate_parent_type(cls, v: Any) -> ParentType:
        """Validate parent type is supported."""
        try:
            if isinstance(v, str):
                v = ParentType(v)
            if not isinstance(v, ParentType):
                raise ValueError(f"Invalid parent type: {v}")
            return v
        except ValueError:
            raise NotionError(message=f"Unsupported parent type: {v}", error_type="validation", status_code=400)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str, info: ValidationInfo) -> str:
        """Validate parent ID is not empty and valid for the parent type."""
        if not isinstance(v, str):
            raise NotionError(message="Parent ID must be a string", error_type="validation", status_code=400)
        if not v.strip():
            raise NotionError(message="Parent ID cannot be empty", error_type="validation", status_code=400)
        # Get parent type from validation context
        parent_type = info.data.get("type")
        if parent_type == ParentType.WORKSPACE and v != ParentType.WORKSPACE:
            raise NotionError(message="Workspace parent cannot have an ID", error_type="validation", status_code=400)
        if len(v) > 100:  # Reasonable max length for Notion IDs
            raise NotionError(message="Parent ID exceeds maximum length", error_type="validation", status_code=400)
        return v.strip()

    @model_validator(mode="after")
    def validate_parent_consistency(self) -> "PageParent":
        """Validate parent type and ID consistency."""
        if self.type == ParentType.WORKSPACE and self.id != ParentType.WORKSPACE:
            raise NotionError(
                message="Workspace parent must have 'workspace' as ID", error_type="validation", status_code=400
            )
        return self

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API request format."""
        if self.type == ParentType.WORKSPACE:
            return {"type": self.type}
        return {"type": self.type, self.type: self.id}

    @classmethod
    def from_notion_format(cls, parent: Dict[str, Any]) -> "PageParent":
        """Create PageParent from Notion API response format."""
        try:
            parent_type = parent.get("type")
            if not parent_type:
                raise NotionError(message="Missing parent type", error_type="validation", status_code=400)

            try:
                parent_type_enum = ParentType(parent_type)
            except ValueError:
                raise NotionError(
                    message=f"Invalid parent type: {parent_type}", error_type="validation", status_code=400
                )
            parent_id = parent.get(parent_type) if parent_type != ParentType.WORKSPACE else ParentType.WORKSPACE
            return cls(type=parent_type_enum, id=parent_id)
        except Exception as e:
            if isinstance(e, NotionError):
                raise e
            raise NotionError(message=f"Invalid parent data: {str(e)}", error_type="validation", status_code=400)


class Parent(BaseModel):
    """Parent model."""

    type: str = Field(..., description="Parent type")
    id: Optional[str] = Field(None, description="Parent ID")
    title: Optional[str] = Field(None, description="Parent title")

    @classmethod
    def from_notion_format(cls, parent: Dict[str, Any]) -> "Parent":
        """Create Parent from Notion format."""
        return cls(
            type=parent.get("type", "unknown"),
            id=parent.get("database_id") or parent.get("page_id"),
            title=parent.get("title", "Unknown"),
        )


class DateProperty(BaseModel):
    """Date property model."""

    start: str
    end: Optional[str] = None


class PageProperties(BaseModel):
    """Page properties model."""

    title: str = Field(..., description="Page title", min_length=1)
    description: Optional[str] = Field(None, description="Page description")
    status: Optional[str] = Field(None, description="Page status")
    tags: Optional[List[str]] = Field(None, description="Page tags")
    url: Optional[str] = Field(None, description="Page URL")
    email: Optional[str] = Field(None, description="Page email")
    phone: Optional[str] = Field(None, description="Page phone")
    date: Optional[datetime] = Field(None, description="Page date")
    number: Optional[float] = Field(None, description="Page number")
    checkbox: Optional[bool] = Field(None, description="Page checkbox")
    select: Optional[str] = Field(None, description="Page select")
    multi_select: Optional[List[str]] = Field(None, description="Page multi-select")
    files: Optional[List[str]] = Field(None, description="Page files")
    relation: Optional[List[str]] = Field(None, description="Page relation")
    formula: Optional[str] = Field(None, description="Page formula")
    rollup: Optional[str] = Field(None, description="Page rollup")
    people: Optional[List[str]] = Field(None, description="Page people")
    created_time: Optional[datetime] = Field(None, description="Page created time")
    created_by: Optional[str] = Field(None, description="Page created by")
    last_edited_time: Optional[datetime] = Field(None, description="Page last edited time")
    last_edited_by: Optional[str] = Field(None, description="Page last edited by")
    parent: Optional[Parent] = Field(None, description="Page parent")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Page properties")

    model_config = ConfigDict(strict=True, populate_by_name=True, validate_assignment=True)

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion format."""
        properties = {}

        if self.title:
            properties["title"] = {"title": [{"text": {"content": self.title}}]}

        if self.description:
            properties["description"] = {"rich_text": [{"text": {"content": self.description}}]}

        if self.status:
            properties["status"] = {"select": {"name": self.status}}

        if self.tags:
            properties["tags"] = {"multi_select": [{"name": tag} for tag in self.tags]}

        if self.url:
            properties["url"] = {"url": self.url}

        if self.email:
            properties["email"] = {"email": self.email}

        if self.phone:
            properties["phone"] = {"phone_number": self.phone}

        if self.date:
            properties["date"] = {"date": {"start": self.date.isoformat()}}

        if self.number:
            properties["number"] = {"number": self.number}

        if self.checkbox is not None:
            properties["checkbox"] = {"checkbox": self.checkbox}

        if self.select:
            properties["select"] = {"select": {"name": self.select}}

        if self.multi_select:
            properties["multi_select"] = {"multi_select": [{"name": option} for option in self.multi_select]}

        if self.files:
            properties["files"] = {"files": [{"name": file} for file in self.files]}

        if self.relation:
            properties["relation"] = {"relation": [{"id": page_id} for page_id in self.relation]}

        if self.formula:
            properties["formula"] = {"formula": {"string": self.formula}}

        if self.rollup:
            properties["rollup"] = {"rollup": {"string": self.rollup}}

        if self.people:
            properties["people"] = {"people": [{"id": user_id} for user_id in self.people]}

        if self.created_time:
            properties["created_time"] = {"created_time": self.created_time.isoformat()}

        if self.created_by:
            properties["created_by"] = {"created_by": {"id": self.created_by}}

        if self.last_edited_time:
            properties["last_edited_time"] = {"last_edited_time": self.last_edited_time.isoformat()}

        if self.last_edited_by:
            properties["last_edited_by"] = {"last_edited_by": {"id": self.last_edited_by}}

        return properties

    def merge_properties(self, other: "PageProperties") -> "PageProperties":
        """Merge properties from another PageProperties instance."""
        merged_data = self.model_dump(exclude_none=True)
        other_data = other.model_dump(exclude_none=True)

        # Update merged data with other data
        for key, value in other_data.items():
            if value is not None:
                if key == "date" and isinstance(value, DateProperty):
                    merged_data[key] = {"start": value.start}
                    if value.end:
                        merged_data[key]["end"] = value.end
                else:
                    merged_data[key] = value

        # Create a new instance with merged data
        return PageProperties(**merged_data)

    @classmethod
    def from_notion_format(cls, properties: Dict[str, Any]) -> "PageProperties":
        """Convert Notion API format to PageProperties."""
        converted_props = {}

        for key, value in properties.items():
            prop_type = value.get("type")
            if prop_type == "title":
                title_array = value.get("title", [])
                if title_array:
                    text_obj = title_array[0].get("text", {})
                    converted_props["title"] = text_obj.get("content", "")
            elif prop_type == "number":
                converted_props["number"] = value.get("number")
            elif prop_type == "select":
                select_obj = value.get("select", {})
                if select_obj:
                    converted_props["select"] = {"name": select_obj.get("name", "")}
            elif prop_type == "multi_select":
                multi_select = value.get("multi_select", [])
                converted_props["multi_select"] = [{"name": item.get("name", "")} for item in multi_select]
            elif prop_type == "date":
                date_obj = value.get("date", {})
                if date_obj:
                    converted_props["date"] = DateProperty(
                        start=date_obj.get("start", ""), end=date_obj.get("end") if date_obj.get("end") else None
                    )
            elif prop_type == "checkbox":
                converted_props["checkbox"] = value.get("checkbox", False)
            elif prop_type == "url":
                converted_props["url"] = value.get("url", "")
            elif prop_type == "email":
                converted_props["email"] = value.get("email", "")
            elif prop_type == "phone_number":
                converted_props["phone"] = value.get("phone_number", "")

        try:
            return cls(**converted_props)
        except ValidationError as e:
            raise NotionError(
                message=f"Validation error during converting properties: {e}", error_type="validation", status_code=400
            )


class RichText(BaseModel):
    """Rich text formatting options."""

    content: str = Field(..., description="Text content", min_length=1)
    bold: Optional[bool] = Field(None, description="Bold formatting")
    italic: Optional[bool] = Field(None, description="Italic formatting")
    strikethrough: Optional[bool] = Field(None, description="Strikethrough formatting")
    underline: Optional[bool] = Field(None, description="Underline formatting")
    code: Optional[bool] = Field(None, description="Code formatting")
    color: Optional[str] = Field(None, description="Text color")

    model_config = ConfigDict(strict=True, populate_by_name=True, validate_assignment=True)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content is not empty."""
        if not v.strip():
            raise NotionError(message="Rich text content cannot be empty", error_type="validation", status_code=400)
        return v

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Validate color if provided."""
        if v is not None and not v.strip():
            raise NotionError(message="Color value cannot be empty", error_type="validation", status_code=400)
        return v

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API rich text format."""
        try:
            text_format = {"type": "text", "text": {"content": self.content}}

            annotations = {}
            for field in ["bold", "italic", "strikethrough", "underline", "code", "color"]:
                value = getattr(self, field)
                if value is not None:
                    annotations[field] = value

            if annotations:
                text_format["annotations"] = annotations

            return text_format
        except Exception as e:
            raise NotionError(
                message=f"Failed to convert rich text to Notion format: {str(e)}",
                error_type="conversion",
                status_code=400,
            )

    @classmethod
    def from_notion_format(cls, data: Dict[str, Any]) -> "RichText":
        """Create RichText from Notion API format."""
        try:
            if not isinstance(data, dict):
                raise NotionError(message="Invalid rich text data format", error_type="validation", status_code=400)

            text_data = data.get("text", {})
            if not isinstance(text_data, dict):
                raise NotionError(message="Invalid text data format", error_type="validation", status_code=400)

            content = text_data.get("content")
            if not content:
                raise NotionError(message="Missing required field: content", error_type="validation", status_code=400)

            annotations = data.get("annotations", {})
            if not isinstance(annotations, dict):
                raise NotionError(message="Invalid annotations format", error_type="validation", status_code=400)

            return cls(
                content=content,
                bold=annotations.get("bold"),
                italic=annotations.get("italic"),
                strikethrough=annotations.get("strikethrough"),
                underline=annotations.get("underline"),
                code=annotations.get("code"),
                color=annotations.get("color"),
            )
        except Exception as e:
            if isinstance(e, NotionError):
                raise e
            raise NotionError(message=f"Invalid rich text data: {str(e)}", error_type="validation", status_code=400)


class BlockContent(BaseModel):
    """Base model for block content."""

    type: BlockType = Field(..., description="Type of block")
    content: Dict[str, Any] = Field(default_factory=dict, description="Block content")
    text: Optional[str] = Field(None, description="Plain text content")
    rich_text: Optional[List[RichText]] = Field(None, description="Rich text content")
    checked: Optional[bool] = Field(None, description="Checkbox state for to-do blocks")
    code: Optional[str] = Field(None, description="Code content for code blocks")
    language: Optional[str] = Field(None, description="Programming language for code blocks")
    color: Optional[str] = Field(None, description="Color for callout blocks")
    children: Optional[List["BlockContent"]] = Field(None, description="Nested blocks")

    model_config = ConfigDict(strict=True, populate_by_name=True, validate_assignment=True)

    @field_validator("type", mode="before")
    @classmethod
    def validate_block_type(cls, v: Any) -> BlockType:
        """Validate block type is supported."""
        try:
            if isinstance(v, str):
                v = BlockType(v)
            if not isinstance(v, BlockType):
                raise ValueError(f"Invalid block type: {v}")
            return v
        except ValueError as e:
            raise NotionError(message=f"Unsupported block type: {v}", error_type="validation", status_code=400) from e

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate text content."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise NotionError(message="Text content must be a string", error_type="validation", status_code=400)
        return v.strip()

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate code content."""
        if v is None:
            return None
        if not isinstance(v, str):
            raise NotionError(message="Code content must be a string", error_type="validation", status_code=400)
        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate language is provided for code blocks."""
        if info.data.get("type") == BlockType.CODE:
            if info.data.get("code") and not v:
                raise NotionError(
                    message="Language is required for code blocks", error_type="validation", status_code=400
                )
            if v and not isinstance(v, str):
                raise NotionError(message="Language must be a string", error_type="validation", status_code=400)
        return v

    @model_validator(mode="after")
    def validate_block_content(self) -> "BlockContent":
        """Validate block content based on type."""
        if self.type == BlockType.CODE:
            if self.code and not self.language:
                raise NotionError(
                    message="Language is required for code blocks", error_type="validation", status_code=400
                )
            if self.language and not self.code:
                raise NotionError(
                    message="Code content is required when language is specified",
                )

        # Ensure at least one content type is provided
        has_content = bool(self.text or self.rich_text or self.code)
        if not has_content and self.type not in [BlockType.DIVIDER]:
            raise NotionError(
                message=f"Content is required for block type: {self.type}", error_type="validation", status_code=400
            )

        return self

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API request format."""
        try:
            block_data = {
                "type": self.type,
                self.type: {"rich_text": []},
            }

            # Handle rich text content
            if self.rich_text:
                block_data[self.type]["rich_text"] = [text.to_notion_format() for text in self.rich_text]
            elif self.text:
                block_data[self.type]["rich_text"] = [RichText(content=self.text).to_notion_format()]
            elif self.code:
                block_data[self.type]["rich_text"] = [RichText(content=self.code).to_notion_format()]
            else:
                block_data[self.type]["rich_text"] = [RichText(content=" ").to_notion_format()]

            # Add block-specific fields
            if self.type == BlockType.CODE:
                block_data[self.type]["language"] = self.language or "plain text"

            if self.type == BlockType.TO_DO and self.checked is not None:
                block_data[self.type]["checked"] = self.checked

            if self.type == BlockType.CALLOUT and self.color:
                block_data[self.type]["color"] = self.color

            # Handle nested blocks
            if self.children:
                block_data["has_children"] = True
                block_data["children"] = [child.to_notion_format() for child in self.children]

            return block_data
        except Exception as e:
            raise NotionError(
                message=f"Failed to convert block to Notion format: {str(e)}", error_type="conversion", status_code=400
            )

    @classmethod
    def from_notion_format(cls, data: Dict[str, Any]) -> "BlockContent":
        """Create BlockContent from Notion API format."""
        try:
            if not isinstance(data, dict):
                raise NotionError(message="Invalid block data format", error_type="validation", status_code=400)

            block_type = data.get("type")
            if not block_type:
                raise NotionError(message="Missing required field: type", error_type="validation", status_code=400)

            try:
                block_type_enum = BlockType(block_type)
            except ValueError:
                raise NotionError(
                    message=f"Unsupported block type: {block_type}", error_type="validation", status_code=400
                )

            block_content = data.get(block_type, {})
            if not isinstance(block_content, dict):
                raise NotionError(message="Invalid block content format", error_type="validation", status_code=400)

            # Extract rich text content
            rich_text_data = block_content.get("rich_text", [])
            rich_text = [RichText.from_notion_format(rt) for rt in rich_text_data] if rich_text_data else None

            # Create block instance
            block = cls(
                type=block_type_enum,
                rich_text=rich_text,
                checked=block_content.get("checked"),
                code=block_content.get("code"),
                language=block_content.get("language"),
                color=block_content.get("color"),
            )

            # Handle nested blocks
            if data.get("has_children") and data.get("children"):
                block.children = [cls.from_notion_format(child) for child in data["children"]]

            return block
        except Exception as e:
            if isinstance(e, NotionError):
                raise e
            raise NotionError(message=f"Invalid block data: {str(e)}", error_type="validation", status_code=400)

    @classmethod
    def create_batch(cls, blocks: List["BlockContent"]) -> List[Dict[str, Any]]:
        """Create multiple blocks in Notion format."""
        try:
            return [block.to_notion_format() for block in blocks]
        except Exception as e:
            if isinstance(e, NotionError):
                raise e
            raise NotionError(
                message=f"Failed to create block batch: {str(e)}", error_type="conversion", status_code=400
            )


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""

    has_more: bool = Field(False, description="Whether there are more results available")
    next_cursor: Optional[str] = Field(None, description="Cursor for the next page of results")
    prev_cursor: Optional[str] = Field(None, description="Cursor for the previous page of results")
    total_results: Optional[int] = Field(None, description="Total number of results if known")

    model_config = ConfigDict(strict=True, populate_by_name=True, validate_assignment=True)

    @field_validator("next_cursor", "prev_cursor")
    @classmethod
    def validate_cursor(cls, v: Optional[str]) -> Optional[str]:
        """Validate cursor is not empty if provided."""
        if v is not None and not v.strip():
            raise NotionError(message="Cursor value cannot be empty", error_type="validation", status_code=400)
        return v

    @field_validator("total_results")
    @classmethod
    def validate_total_results(cls, v: Optional[int]) -> Optional[int]:
        """Validate total results is non-negative if provided."""
        if v is not None and v < 0:
            raise NotionError(message="Total results cannot be negative", error_type="validation", status_code=400)
        return v

    @classmethod
    def from_notion_response(cls, response: Dict[str, Any]) -> "PaginationMetadata":
        """Create pagination metadata from Notion API response."""
        try:
            if not isinstance(response, dict):
                raise NotionError(message="Invalid response format", error_type="validation", status_code=400)

            return cls(
                has_more=response.get("has_more", False),
                next_cursor=response.get("next_cursor"),
                total_results=response.get("total_results"),
            )
        except Exception as e:
            if isinstance(e, NotionError):
                raise e
            raise NotionError(
                message=f"Failed to create pagination metadata: {str(e)}", error_type="validation", status_code=400
            )

    def to_notion_format(self) -> Dict[str, Any]:
        """Convert to Notion API request format."""
        try:
            data = {"has_more": self.has_more}

            if self.next_cursor:
                data["next_cursor"] = self.next_cursor
            if self.total_results is not None:
                data["total_results"] = self.total_results

            return data
        except Exception as e:
            raise NotionError(
                message=f"Failed to convert pagination metadata to Notion format: {str(e)}",
                error_type="conversion",
                status_code=400,
            )


class PageResponse(BaseModel):
    """Response model for Notion page operations."""

    id: str = Field(..., description="Page ID")
    object: str = Field("page", description="Object type")
    title: str = Field("Untitled", description="Page title")
    url: Optional[str] = Field(None, description="Page URL")
    created_time: str = Field(..., description="Creation timestamp")
    last_edited_time: str = Field(..., description="Last edit timestamp")
    parent: Dict[str, Any] = Field(..., description="Parent information")
    properties: Dict[str, Any] = Field(..., description="Page properties")
    archived: bool = Field(False, description="Whether the page is archived")

    model_config = ConfigDict(strict=True, populate_by_name=True, validate_assignment=True)

    @field_validator("object")
    @classmethod
    def validate_object_type(cls, v: str) -> str:
        """Validate object type is 'page'."""
        if v != "page":
            raise NotionError(message="Invalid object type", error_type="validation", status_code=400)
        return v

    @classmethod
    def from_notion_page(cls, page: Dict[str, Any]) -> "PageResponse":
        """Create PageResponse from Notion page object."""
        try:
            if not page.get("id"):
                raise NotionError(
                    message="Missing required field: id",
                    error_type="validation",
                    status_code=400,
                )

            # Extract title from properties
            title = "Untitled"
            properties = page.get("properties", {})
            if properties and isinstance(properties, dict):
                title_prop = properties.get("title", {})
                if title_prop and isinstance(title_prop, dict):
                    title_content = title_prop.get("title", [])
                    if title_content and isinstance(title_content, list):
                        first_title = title_content[0]
                        if first_title and isinstance(first_title, dict):
                            text = first_title.get("text", {})
                            if text and isinstance(text, dict):
                                content = text.get("content")
                                if content and isinstance(content, str):
                                    title = content

            return cls(
                id=page["id"],
                object=page.get("object", "page"),
                title=title,
                url=page.get("url"),
                created_time=page.get("created_time"),
                last_edited_time=page.get("last_edited_time"),
                parent=page.get("parent", {}),
                properties=properties,
                archived=page.get("archived", False),
            )

        except Exception as e:
            if isinstance(e, NotionError):
                raise e
            raise NotionError(message=f"Invalid page data: {str(e)}", error_type="validation", status_code=400)

    def get_property(self, name: str) -> Any:
        """Get a property value by name."""
        prop = self.properties.get(name, {})
        if not prop:
            return None

        prop_type = prop.get("type")
        if not prop_type:
            return None

        if prop_type == "title":
            return self.title
        elif prop_type == "rich_text":
            rich_text = prop.get("rich_text", [])
            return "".join(text.get("plain_text", "") for text in rich_text)
        elif prop_type == "number":
            return prop.get("number")
        elif prop_type == "select":
            select = prop.get("select", {})
            return select.get("name")
        elif prop_type == "multi_select":
            multi_select = prop.get("multi_select", [])
            return [item.get("name") for item in multi_select if item.get("name")]
        elif prop_type == "date":
            date = prop.get("date", {})
            return {"start": date.get("start"), "end": date.get("end")}
        elif prop_type == "checkbox":
            return prop.get("checkbox", False)
        elif prop_type == "url":
            return prop.get("url")
        elif prop_type == "email":
            return prop.get("email")
        elif prop_type == "phone":
            return prop.get("phone")
        else:
            return None

    def is_accessible(self) -> bool:
        """Check if the page is accessible (not archived)."""
        return not self.archived
