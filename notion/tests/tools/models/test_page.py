"""
Tests for Notion page models.
"""

from typing import Any, Dict

import pytest

from notion.tools.models.page import (
    BlockContent,
    BlockType,
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
        """Test invalid parent type."""
        with pytest.raises(ValueError, match="Unsupported parent type"):
            PageParent(type="invalid", id="test-id")

    def test_from_notion_format(self):
        """Test creating from Notion format."""
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


class TestPageProperties:
    """Test suite for PageProperties model."""

    def test_valid_properties(self, sample_page_properties):
        """Test valid properties creation."""
        assert sample_page_properties.title == "Test Page"
        assert sample_page_properties.number == 42
        assert sample_page_properties.select == {"name": "Option 1"}

    def test_from_notion_format(self):
        """Test creating from Notion format."""
        notion_data = {
            "title": {"title": [{"text": {"content": "Test Title"}}]},
            "number": {"type": "number", "number": 42},
            "select": {"type": "select", "select": {"name": "Option 1"}},
        }
        props = PageProperties.from_notion_format(notion_data)
        assert props.title == "Test Title"
        assert props.number == 42
        assert props.select == {"name": "Option 1"}

    def test_to_notion_format(self, sample_page_properties):
        """Test converting to Notion format."""
        notion_format = sample_page_properties.to_notion_format()
        assert "title" in notion_format
        assert notion_format["title"]["title"][0]["text"]["content"] == "Test Page"
        assert notion_format["number"]["number"] == 42

    def test_merge_properties(self):
        """Test merging properties."""
        base = PageProperties(title="Base Title", number=42)
        other = PageProperties(title="New Title", select={"name": "Option"})
        merged = base.merge_properties(other)

        assert merged.title == "New Title"
        assert merged.number == 42
        assert merged.select == {"name": "Option"}


class TestPageResponse:
    """Test suite for PageResponse model."""

    def test_from_notion_page(self, sample_page):
        """Test creating from Notion page."""
        response = PageResponse.from_notion_page(sample_page)
        assert response.id == "test-page-id"
        assert response.title == "Test Page"
        assert response.parent.type == ParentType.PAGE

    def test_invalid_page_data(self):
        """Test handling invalid page data."""
        with pytest.raises(ValueError, match="Missing required field"):
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


class TestBlockContent:
    """Test suite for BlockContent model."""

    def test_valid_block(self, sample_block_content):
        """Test valid block creation."""
        block = sample_block_content[0]
        assert block.type == BlockType.PARAGRAPH
        assert block.text == "Test paragraph"

    def test_invalid_block_type(self):
        """Test invalid block type."""
        with pytest.raises(ValueError, match="Unsupported block type"):
            BlockContent(type="invalid", text="Test")

    def test_to_notion_format(self):
        """Test converting to Notion format."""
        block = BlockContent(
            type=BlockType.PARAGRAPH,
            text="Test",
            rich_text=[RichText(content="Test", bold=True)],
        )
        notion_format = block.to_notion_format()

        assert notion_format["type"] == "paragraph"
        assert notion_format["paragraph"]["rich_text"][0]["annotations"]["bold"] is True

    def test_create_batch(self, sample_block_content):
        """Test creating batch of blocks."""
        notion_blocks = BlockContent.create_batch(sample_block_content)
        assert len(notion_blocks) == 3
        assert all(isinstance(block, dict) for block in notion_blocks)


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
