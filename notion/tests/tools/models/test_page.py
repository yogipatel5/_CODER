"""
Tests for Notion page models.
"""

from typing import Any, Dict, List

import pytest
from pydantic import ValidationError

from notion.tools.models.page import (
    BlockContent,
    BlockType,
    DateProperty,
    NotionError,
    PageParent,
    PageProperties,
    PageResponse,
    ParentType,
    PropertyType,
    RichText,
)


class TestPageParent:
    """Test suite for PageParent model."""

    def test_valid_parent(self):
        """Test valid parent creation."""
        parent = PageParent(type=ParentType.PAGE, id="test-page-id")
        assert parent.type == ParentType.PAGE
        assert parent.id == "test-page-id"

    def test_invalid_parent_type(self):
        """Test invalid parent type validation."""
        with pytest.raises(NotionError) as exc_info:
            PageParent(type="invalid", id="test-id")
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "Unsupported parent type" in str(exc_info.value)

    def test_empty_parent_id(self):
        """Test empty parent ID validation."""
        from pydantic import ValidationError

        # Test empty string
        with pytest.raises(ValidationError) as exc_info:
            PageParent(type=ParentType.PAGE, id="")
        error = exc_info.value.errors()[0]
        assert error["type"] == "string_too_short"
        assert "at least 1 character" in error["msg"]

        # Test whitespace string
        with pytest.raises(NotionError) as exc_info:
            PageParent(type=ParentType.PAGE, id="   ")
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "Parent ID cannot be empty" in str(exc_info.value)

    def test_to_notion_format(self):
        """Test converting to Notion format."""
        # Test page parent
        page_parent = PageParent(type=ParentType.PAGE, id="test-page-id")
        page_format = page_parent.to_notion_format()
        assert page_format == {"type": "page_id", "page_id": "test-page-id"}

        # Test workspace parent
        workspace_parent = PageParent(type=ParentType.WORKSPACE, id=ParentType.WORKSPACE)
        workspace_format = workspace_parent.to_notion_format()
        assert workspace_format == {"type": "workspace"}

        # Test database parent
        db_parent = PageParent(type=ParentType.DATABASE, id="test-db-id")
        db_format = db_parent.to_notion_format()
        assert db_format == {"type": "database_id", "database_id": "test-db-id"}

    def test_from_notion_format_page(self):
        """Test creating page parent from Notion format."""
        notion_data = {"type": "page_id", "page_id": "test-page-id"}
        parent = PageParent.from_notion_format(notion_data)
        assert parent.type == ParentType.PAGE
        assert parent.id == "test-page-id"

    def test_from_notion_format_workspace(self):
        """Test creating workspace parent from Notion format."""
        notion_data = {"type": "workspace"}
        parent = PageParent.from_notion_format(notion_data)
        assert parent.type == ParentType.WORKSPACE
        assert parent.id == ParentType.WORKSPACE

    def test_from_notion_format_missing_type(self):
        """Test error handling for missing type."""
        with pytest.raises(NotionError) as exc_info:
            PageParent.from_notion_format({})
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "Missing parent type" in str(exc_info.value)

    def test_from_notion_format_invalid_type(self):
        """Test error handling for invalid type."""
        with pytest.raises(NotionError) as exc_info:
            PageParent.from_notion_format({"type": "invalid"})
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "Invalid parent type" in str(exc_info.value)

    def test_from_notion_format_missing_id(self):
        """Test error handling for missing ID."""
        with pytest.raises(NotionError) as exc_info:
            PageParent.from_notion_format({"type": "page_id"})
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "Missing parent ID" in str(exc_info.value)


class TestPageProperties:
    """Test suite for PageProperties model."""

    def test_valid_properties(self, sample_page_properties):
        """Test valid properties creation."""
        props = PageProperties(**sample_page_properties)
        assert props.title == sample_page_properties["title"]
        assert props.number == sample_page_properties["number"]
        assert props.select == sample_page_properties["select"]

    def test_empty_title(self):
        """Test empty title validation."""
        from pydantic import ValidationError

        # Test empty string
        with pytest.raises(ValidationError) as exc_info:
            PageProperties(title="")
        error = exc_info.value.errors()[0]
        assert error["type"] == "string_too_short"
        assert "at least 1 character" in error["msg"]

        # Test whitespace string
        with pytest.raises(NotionError) as exc_info:
            PageProperties(title="   ")
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "Title cannot be empty" in str(exc_info.value)

    def test_invalid_number(self):
        """Test invalid number validation."""
        with pytest.raises(NotionError) as exc_info:
            PageProperties(number="invalid")
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "could not convert string to float" in str(exc_info.value).lower()

    @pytest.mark.parametrize(
        "property_type,valid_value,expected_value",
        [
            ("number", 42, 42.0),
            ("number", "42", 42.0),
            ("number", 42.5, 42.5),
            ("select", {"name": "Option 1"}, {"name": "Option 1"}),
            ("multi_select", [{"name": "Tag 1"}, {"name": "Tag 2"}], [{"name": "Tag 1"}, {"name": "Tag 2"}]),
            ("date", {"start": "2024-01-01"}, DateProperty(start="2024-01-01")),
            ("date", {"start": "2024-01-01", "end": "2024-01-31"}, DateProperty(start="2024-01-01", end="2024-01-31")),
            ("checkbox", True, True),
            ("checkbox", False, False),
            ("url", "https://example.com", "https://example.com"),
            ("email", "test@example.com", "test@example.com"),
            ("phone", "+1234567890", "+1234567890"),
        ],
    )
    def test_valid_property_values(self, property_type, valid_value, expected_value):
        """Test valid values for different property types."""
        props = PageProperties(title="Test", **{property_type: valid_value})
        assert getattr(props, property_type) == expected_value

    @pytest.mark.parametrize(
        "property_type,invalid_value,expected_error",
        [
            ("number", "invalid", "could not convert string to float"),
            ("select", {"invalid": "format"}, "Select must have a 'name' field"),
            ("multi_select", [{"invalid": "format"}], "Multi-select items must have a 'name' field"),
            ("date", {"invalid": "format"}, "Missing required field: start"),
            ("date", {"start": ""}, "String should have at least 1 character"),
            ("url", "invalid-url", "Invalid URL format"),
            ("email", "invalid-email", "Invalid email format"),
            ("phone", "", "Phone number cannot be empty"),
        ],
    )
    def test_invalid_property_values(self, property_type, invalid_value, expected_error):
        """Test invalid values for different property types."""
        with pytest.raises((NotionError, ValidationError)) as exc_info:
            PageProperties(title="Test", **{property_type: invalid_value})
        error_message = str(exc_info.value).lower()
        expected_error = expected_error.lower()
        assert expected_error == error_message

    @pytest.mark.parametrize(
        "notion_format,expected_props",
        [
            (
                {
                    "title": {"type": "title", "title": [{"text": {"content": "Test Title"}}]},
                    "number": {"type": "number", "number": 42},
                    "select": {"type": "select", "select": {"name": "Option 1"}},
                },
                {"title": "Test Title", "number": 42, "select": {"name": "Option 1"}},
            ),
            (
                {
                    "title": {"type": "title", "title": [{"text": {"content": "Test Title"}}]},
                    "multi_select": {
                        "type": "multi_select",
                        "multi_select": [{"name": "Tag 1"}, {"name": "Tag 2"}],
                    },
                    "date": {"type": "date", "date": {"start": "2024-01-01", "end": "2024-01-31"}},
                },
                {
                    "title": "Test Title",
                    "multi_select": [{"name": "Tag 1"}, {"name": "Tag 2"}],
                    "date": DateProperty(start="2024-01-01", end="2024-01-31"),
                },
            ),
        ],
    )
    def test_from_notion_format_variations(self, notion_format, expected_props):
        """Test converting different Notion format variations to PageProperties."""
        props = PageProperties.from_notion_format(notion_format)
        for key, value in expected_props.items():
            assert getattr(props, key) == value

    @pytest.mark.parametrize(
        "props,expected_notion_format",
        [
            (
                {"title": "Test Title", "number": 42},
                {
                    "title": {
                        "type": "title",
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": "Test Title"},
                                "plain_text": "Test Title",
                                "href": None,
                            }
                        ],
                    },
                    "number": {"type": "number", "number": 42},
                },
            ),
            (
                {
                    "title": "Test Title",
                    "multi_select": [{"name": "Tag 1"}, {"name": "Tag 2"}],
                    "date": {"start": "2024-01-01", "end": "2024-01-31"},
                },
                {
                    "title": {
                        "type": "title",
                        "title": [
                            {
                                "type": "text",
                                "text": {"content": "Test Title"},
                                "plain_text": "Test Title",
                                "href": None,
                            }
                        ],
                    },
                    "multi_select": {
                        "type": "multi_select",
                        "multi_select": [{"name": "Tag 1"}, {"name": "Tag 2"}],
                    },
                    "date": {
                        "type": "date",
                        "date": {"start": "2024-01-01", "end": "2024-01-31"},
                    },
                },
            ),
        ],
    )
    def test_to_notion_format_variations(self, props, expected_notion_format):
        """Test converting PageProperties to different Notion format variations."""
        page_props = PageProperties(**props)
        notion_format = page_props.to_notion_format()
        assert notion_format == expected_notion_format

    @pytest.mark.parametrize(
        "base_props,update_props,expected_props",
        [
            (
                {"title": "Base Title", "number": 42},
                {"title": "Updated Title", "select": {"name": "Option 1"}},
                {"title": "Updated Title", "number": 42, "select": {"name": "Option 1"}},
            ),
            (
                {"title": "Base Title", "multi_select": [{"name": "Tag 1"}]},
                {
                    "title": "Base Title",
                    "multi_select": [{"name": "Tag 2"}],
                    "date": {"start": "2024-01-01"},
                },
                {
                    "title": "Base Title",
                    "multi_select": [{"name": "Tag 2"}],
                    "date": {"start": "2024-01-01"},
                },
            ),
        ],
    )
    def test_merge_properties_variations(self, base_props, update_props, expected_props):
        """Test merging different property combinations."""
        base = PageProperties(**base_props)
        update = PageProperties(**update_props)
        merged = base.merge_properties(update)

        for key, value in expected_props.items():
            merged_value = getattr(merged, key)
            if key == "date":
                assert isinstance(merged_value, DateProperty)
                assert merged_value.start == value["start"]
                assert merged_value.end == value.get("end")
            else:
                assert merged_value == value


class TestPageResponse:
    """Test suite for PageResponse model."""

    def test_from_notion_page(self, sample_page: Dict[str, Any]):
        """Test creating from Notion page."""
        response = PageResponse.from_notion_page(sample_page)
        assert response.id == "test-page-id"
        assert response.title == "Test Page"
        assert response.parent.type == "database_id"
        assert response.parent.id == "test-db-id"
        assert response.created_time == "2023-01-01T00:00:00.000Z"
        assert response.last_edited_time == "2023-01-01T00:00:00.000Z"
        assert not response.archived

    def test_from_notion_page_no_title(self, sample_page: Dict[str, Any]):
        """Test creating from page without title."""
        del sample_page["properties"]["title"]
        response = PageResponse.from_notion_page(sample_page)
        assert response.title == "Untitled"

    def test_from_notion_page_empty_title(self, sample_page: Dict[str, Any]):
        """Test creating from page with empty title."""
        sample_page["properties"]["title"]["title"] = []
        response = PageResponse.from_notion_page(sample_page)
        assert response.title == "Untitled"

    def test_from_notion_page_invalid_title(self, sample_page: Dict[str, Any]):
        """Test creating from page with invalid title."""
        sample_page["properties"]["title"]["title"][0]["text"]["content"] = ""
        response = PageResponse.from_notion_page(sample_page)
        assert response.title == "Untitled"

    def test_from_notion_page_no_properties(self, sample_page: Dict[str, Any]):
        """Test creating from page without properties."""
        del sample_page["properties"]
        response = PageResponse.from_notion_page(sample_page)
        assert response.title == "Untitled"

    def test_from_notion_page_invalid_properties(self, sample_page: Dict[str, Any]):
        """Test creating from page with invalid properties."""
        sample_page["properties"] = None
        response = PageResponse.from_notion_page(sample_page)
        assert response.title == "Untitled"

    def test_invalid_page_data(self):
        """Test handling invalid page data."""
        with pytest.raises(NotionError, match="Missing required field: id"):
            PageResponse.from_notion_page({})

    def test_get_property(self, sample_page):
        """Test getting property value."""
        response = PageResponse.from_notion_page(sample_page)
        assert response.get_property("title") == "Test Page"

    def test_is_accessible(self, sample_page):
        """Test accessibility check."""
        response = PageResponse.from_notion_page(sample_page)
        assert response.is_accessible() is True

        archived_page = {**sample_page, "archived": True}
        archived_response = PageResponse.from_notion_page(archived_page)
        assert archived_response.is_accessible() is False


@pytest.fixture
def sample_block_content() -> List[BlockContent]:
    """Sample block content for testing."""
    return [
        BlockContent(type=BlockType.PARAGRAPH, text="Test paragraph"),
        BlockContent(type=BlockType.HEADING_1, text="Test heading"),
        BlockContent(type=BlockType.CODE, code="print('hello')", language="python"),
    ]


class TestBlockContent:
    """Test suite for BlockContent model."""

    def test_valid_block(self, sample_block_content):
        """Test valid block creation."""
        block = sample_block_content[0]
        assert block.type == BlockType.PARAGRAPH
        assert block.text == "Test paragraph"

    def test_invalid_block_type(self):
        """Test invalid block type."""
        with pytest.raises(NotionError) as exc_info:
            BlockContent(type="invalid", content={})
        assert exc_info.value.error_type == "validation"
        assert exc_info.value.status_code == 400
        assert "Unsupported block type" in str(exc_info.value)

    def test_to_notion_format(self):
        """Test converting to Notion format."""
        block = BlockContent(type=BlockType.PARAGRAPH, text="Test", rich_text=[RichText(content="Test", bold=True)])
        notion_format = block.to_notion_format()
        assert notion_format["type"] == "paragraph"
        assert notion_format[BlockType.PARAGRAPH]["rich_text"][0]["text"]["content"] == "Test"
        assert notion_format[BlockType.PARAGRAPH]["rich_text"][0]["annotations"]["bold"] is True

    def test_create_batch(self, sample_block_content):
        """Test creating batch of blocks."""
        notion_blocks = BlockContent.create_batch(sample_block_content)
        assert len(notion_blocks) == 3
        assert all(isinstance(block, dict) for block in notion_blocks)
        assert notion_blocks[0]["type"] == "paragraph"
        assert notion_blocks[1]["type"] == "heading_1"
        assert notion_blocks[2]["type"] == "code"


class TestRichText:
    """Test suite for RichText model."""

    def test_valid_rich_text(self):
        """Test valid rich text creation."""
        text = RichText(
            content="Test",
            bold=True,
            italic=True,
            color="red",
        )
        assert text.content == "Test"
        assert text.bold is True
        assert text.italic is True
        assert text.color == "red"

    def test_to_notion_format(self):
        """Test converting to Notion format."""
        text = RichText(
            content="Test",
            bold=True,
            code=True,
        )
        notion_format = text.to_notion_format()

        assert notion_format["type"] == "text"
        assert notion_format["text"]["content"] == "Test"
        assert notion_format["annotations"]["bold"] is True
        assert notion_format["annotations"]["code"] is True
