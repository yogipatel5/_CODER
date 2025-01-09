"""
Tests for Notion management commands.
"""

import json
from io import StringIO
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from notion.management.commands.base import NotionAPI


@pytest.fixture
def mock_notion_api() -> Generator[MagicMock, None, None]:
    """Mock NotionAPI."""
    with patch("notion.management.commands.base.NotionAPI") as mock:
        api = MagicMock(spec=NotionAPI)

        # Mock get_page
        api.get_page.return_value = {
            "id": "test-page-id",
            "properties": {"title": {"title": [{"plain_text": "Test Page"}]}},
            "parent": {"type": "page_id", "page_id": "parent-id"},
            "url": "https://notion.so/test-page",
        }

        # Mock get_block_children
        api.get_block_children.return_value = [
            {"id": "block1", "type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Test content"}]}}
        ]

        # Mock search_pages
        api.search_pages.return_value = [
            {"id": "page1", "properties": {"title": {"title": [{"plain_text": "Page 1"}]}}}
        ]

        # Mock create_page
        api.create_page.return_value = {"id": "new-page-id", "url": "https://notion.so/new-page"}

        yield api


def test_get_page(mock_notion_api: MagicMock) -> None:
    """Test get_page command."""
    out = StringIO()
    call_command("get_page", "test-page-id", stdout=out)
    response = json.loads(out.getvalue())

    # Verify response format
    assert response["success"] is True
    assert "message" in response
    assert "data" in response
    assert "page" in response["data"]
    assert response["data"]["page"]["id"] == "test-page-id"

    # Test with content
    out = StringIO()
    call_command("get_page", "test-page-id", "--include-content", stdout=out)
    response = json.loads(out.getvalue())
    assert "content" in response["data"]
    assert len(response["data"]["content"]) > 0


def test_list_pages(mock_notion_api: MagicMock) -> None:
    """Test list_pages command."""
    out = StringIO()
    call_command("list_pages", stdout=out)
    response = json.loads(out.getvalue())

    assert response["success"] is True
    assert "data" in response
    assert "pages" in response["data"]
    assert "total" in response["data"]
    assert "limit" in response["data"]


def test_update_page_json(mock_notion_api: MagicMock) -> None:
    """Test update_page_json command."""
    test_json = {"properties": {"title": "Updated Title"}}

    out = StringIO()
    call_command("update_page_json", "test-page-id", f"--json-string={json.dumps(test_json)}", stdout=out)
    response = json.loads(out.getvalue())

    assert response["success"] is True
    assert "data" in response
    assert "page_id" in response["data"]
    assert "title" in response["data"]
    assert "url" in response["data"]


def test_manage_blocks(mock_notion_api: MagicMock) -> None:
    """Test manage_blocks command."""
    # Test create block
    out = StringIO()
    call_command("manage_blocks", "create", "test-page-id", "--type=paragraph", "--content=Test content", stdout=out)
    response = json.loads(out.getvalue())

    assert response["success"] is True
    assert "data" in response
    assert "block_id" in response["data"]

    # Test update block
    out = StringIO()
    call_command("manage_blocks", "update", "block1", "--type=paragraph", "--content=Updated content", stdout=out)
    response = json.loads(out.getvalue())

    assert response["success"] is True
    assert "data" in response
    assert "block_id" in response["data"]


def test_error_handling(mock_notion_api: MagicMock) -> None:
    """Test error handling in commands."""
    # Simulate API error
    mock_notion_api.get_page.side_effect = Exception("API Error")

    out = StringIO()
    call_command("get_page", "invalid-id", stdout=out)
    response = json.loads(out.getvalue())

    assert response["success"] is False
    assert "error" in response
    assert "message" in response
    assert "context" in response
