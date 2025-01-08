"""
Tests for the Notion Agent implementation.
"""

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from notion.agent.v2 import NotionDependencies, get_response
from notion.services import NotionService


@pytest.fixture(autouse=True)
def mock_logfire() -> Generator[MagicMock, None, None]:
    """Mock Logfire configuration."""
    with patch("logfire.configure") as mock:
        yield mock


@pytest.fixture
def mock_notion_service() -> MagicMock:
    """Create a mock NotionService."""
    service = MagicMock(spec=NotionService)

    # Mock list_users
    service.list_users.return_value = [{"id": "user1"}, {"id": "user2"}]

    # Mock search_pages
    service.search_pages.return_value = [{"id": "page1"}, {"id": "page2"}]

    # Mock create_page
    service.create_page.return_value = {
        "id": "new-page-id",
        "url": "https://notion.so/new-page",
    }

    return service


def test_create_page(mock_notion_service: MagicMock) -> None:
    """Test creating a new page through the agent."""
    # Arrange
    deps = NotionDependencies(service=mock_notion_service)
    prompt = "Create a new page titled 'Test Page' with content 'This is a test.'"

    # Act
    result = get_response(prompt, deps)
    print(f"\nAgent response: {result}")

    # Assert
    assert result.success
    assert result.message
    assert not result.error

    # Verify service calls
    assert mock_notion_service.create_page.call_count == 1
    create_args = mock_notion_service.create_page.call_args.kwargs
    assert "properties" in create_args
    assert "title" in create_args["properties"]
    title_content = create_args["properties"]["title"]["title"][0]["text"]["content"]
    assert "Test Page" in title_content
