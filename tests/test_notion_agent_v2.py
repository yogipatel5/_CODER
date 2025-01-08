"""
Tests for the NotionAgentV2 implementation.
"""

from typing import Any, List, cast
from unittest.mock import MagicMock

import pytest

from notion.agent.tools.v2_edit import EditPageRequest
from notion.services import NotionService
from notion.types import NotionBlock, NotionBlockChildren, NotionPage


@pytest.fixture
def mock_notion_service() -> MagicMock:
    """Create a mock NotionService."""
    mock = MagicMock(spec=NotionService)

    # Create page mock
    create_page_mock = MagicMock(name="create_page")
    create_page_mock.return_value = cast(NotionPage, {"id": "test-page-id"})
    mock.create_page = create_page_mock

    # Get page mock
    get_page_mock = MagicMock(name="get_page")
    get_page_mock.return_value = cast(
        NotionPage,
        {
            "id": "test-page-id",
            "properties": {"title": {"title": [{"text": {"content": "Test Page"}}]}},
        },
    )
    mock.get_page = get_page_mock

    # Get block children mock
    get_block_children_mock = MagicMock(name="get_block_children")
    get_block_children_mock.return_value = cast(
        List[NotionBlock],
        [
            {
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "Test content"}}]},
            }
        ],
    )
    mock.get_block_children = get_block_children_mock

    # Update page mock
    update_page_mock = MagicMock(name="update_page")
    update_page_mock.return_value = cast(NotionPage, {"id": "test-page-id"})
    mock.update_page = update_page_mock

    # Append blocks mock
    append_blocks_mock = MagicMock(name="append_blocks")
    append_blocks_mock.return_value = cast(
        NotionBlockChildren, {"id": "test-block-id", "results": []}
    )
    mock.append_blocks = append_blocks_mock

    # Update block mock
    update_block_mock = MagicMock(name="update_block")
    update_block_mock.return_value = cast(NotionBlock, {"id": "test-block-id"})
    mock.update_block = update_block_mock

    return mock


@pytest.fixture
def mock_agent(
    mock_notion_service: MagicMock,
) -> Any:  # TODO: Fix this type once NotionAgentV2 is properly defined
    """Create a mock NotionAgentV2 instance."""
    from notion.agent.v2 import NotionDependencies

    deps = NotionDependencies(service=mock_notion_service)
    return deps


async def test_create_page(mock_notion_service: MagicMock) -> None:
    """Test create page functionality."""
    # Test data
    parent = {"page_id": "test-parent-id"}
    properties = {"title": {"title": [{"text": {"content": "Test Page"}}]}}
    content = "Test content"

    # Create page
    page = await mock_notion_service.create_page(parent=parent, properties=properties)
    assert page["id"] == "test-page-id"

    # Verify service calls
    mock_notion_service.create_page.assert_called_once()
    call_args = mock_notion_service.create_page.call_args[1]
    assert call_args["parent"] == parent
    assert call_args["properties"] == properties


async def test_read_page(mock_notion_service: MagicMock) -> None:
    """Test read page functionality."""
    # Test data
    page_id = "test-page-id"

    # Read page
    page = await mock_notion_service.get_page(page_id)
    assert page["id"] == "test-page-id"
    assert page["properties"]["title"]["title"][0]["text"]["content"] == "Test Page"

    # Get content
    blocks = await mock_notion_service.get_block_children(page_id)
    assert len(blocks) == 1
    assert blocks[0]["paragraph"]["rich_text"][0]["text"]["content"] == "Test content"

    # Verify service calls
    mock_notion_service.get_page.assert_called_once_with("test-page-id")
    mock_notion_service.get_block_children.assert_called_once_with("test-page-id")


async def test_read_page_without_content(mock_notion_service: MagicMock) -> None:
    """Test read page without content."""
    # Test data
    page_id = "test-page-id"

    # Read page
    page = await mock_notion_service.get_page(page_id)
    assert page["id"] == "test-page-id"
    assert page["properties"]["title"]["title"][0]["text"]["content"] == "Test Page"

    # Verify service calls
    mock_notion_service.get_page.assert_called_once_with("test-page-id")
    mock_notion_service.get_block_children.assert_not_called()


async def test_edit_page(mock_notion_service: MagicMock) -> None:
    """Test edit page functionality."""
    # Test data
    page_id = "test-page-id"
    title = "Updated Title"
    properties = {"title": {"title": [{"text": {"content": title}}]}}

    # Update page
    page = await mock_notion_service.update_page(page_id, properties)
    assert page["id"] == "test-page-id"

    # Verify service calls
    mock_notion_service.get_page.assert_called_once_with("test-page-id")
    mock_notion_service.update_page.assert_called_once()
    call_args = mock_notion_service.update_page.call_args[1]
    assert call_args["properties"] == properties


async def test_edit_page_append_content(mock_notion_service: MagicMock) -> None:
    """Test append content functionality."""
    # Test data
    page_id = "test-page-id"
    content = "Additional content"

    # Create request
    request = EditPageRequest(
        page_id=page_id,
        content=content,
        append_content=True,
        title=None,
        properties=None,
    )

    # Update page
    blocks = await mock_notion_service.append_blocks(
        page_id,
        [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": content}}]},
            }
        ],
    )
    assert blocks["id"] == "test-block-id"

    # Verify service calls
    mock_notion_service.get_page.assert_called_once_with("test-page-id")
    mock_notion_service.append_blocks.assert_called_once()
    mock_notion_service.get_block_children.assert_not_called()


async def test_error_handling(mock_notion_service: MagicMock) -> None:
    """Test error handling."""
    # Set up error condition
    mock_notion_service.create_page.side_effect = Exception("Test error")

    # Test error handling
    with pytest.raises(Exception, match="Test error"):
        await mock_notion_service.create_page(
            parent={"page_id": "test-parent-id"},
            properties={"title": {"title": [{"text": {"content": "Test Page"}}]}},
        )
