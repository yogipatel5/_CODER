from unittest.mock import MagicMock

import pytest

from notion.agent.base import AgentConfig, NotionAgent
from notion.services import NotionService


@pytest.fixture
def mock_notion_service() -> MagicMock:
    """Create a mock NotionService."""
    mock = MagicMock(spec=NotionService)

    # Create page mock
    create_page_mock = MagicMock(name="create_page")
    create_page_mock.return_value = {"id": "test-page-id"}
    mock.create_page = create_page_mock

    # Get page mock
    get_page_mock = MagicMock(name="get_page")
    get_page_mock.return_value = {
        "id": "test-page-id",
        "properties": {"title": {"title": [{"text": {"content": "Test Page"}}]}},
    }
    mock.get_page = get_page_mock

    # Get block children mock
    get_block_children_mock = MagicMock(name="get_block_children")
    get_block_children_mock.return_value = [
        {
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": "Test content"}}]},
        }
    ]
    mock.get_block_children = get_block_children_mock

    # Update page mock
    update_page_mock = MagicMock(name="update_page")
    update_page_mock.return_value = {"id": "test-page-id"}
    mock.update_page = update_page_mock

    # Append blocks mock
    append_blocks_mock = MagicMock(name="append_blocks")
    append_blocks_mock.return_value = {"id": "test-block-id"}
    mock.append_blocks = append_blocks_mock

    # Update block mock
    update_block_mock = MagicMock(name="update_block")
    update_block_mock.return_value = {"id": "test-block-id"}
    mock.update_block = update_block_mock

    return mock


@pytest.fixture
def agent(mock_notion_service: MagicMock) -> NotionAgent:
    """Create a NotionAgent instance for testing."""
    config = AgentConfig(service=mock_notion_service, max_retries=1, timeout=5)
    return NotionAgent(config)


def test_agent_initialization(agent: NotionAgent) -> None:
    """Test agent initialization."""
    assert agent.service is not None
    assert len(agent.tools) == 3  # CreatePageTool, ReadPageTool, and EditPageTool
    assert "create_page" in agent.tools
    assert "read_page" in agent.tools
    assert "edit_page" in agent.tools


async def test_create_page_tool(
    agent: NotionAgent, mock_notion_service: MagicMock
) -> None:
    """Test create page tool."""
    tool = agent.tools["create_page"]
    result = await tool.execute(
        title="Test Page",
        content="Test content",
    )

    assert result.success is True
    assert isinstance(result.data, dict)
    assert result.data.get("id") == "test-page-id"
    assert result.error is None

    assert mock_notion_service.create_page.call_count == 1
    assert mock_notion_service.append_blocks.call_count == 1


async def test_read_page_tool(
    agent: NotionAgent, mock_notion_service: MagicMock
) -> None:
    """Test read page tool."""
    tool = agent.tools["read_page"]
    result = await tool.execute(
        page_id="test-page-id",
        include_content=True,
    )

    assert result.success is True
    assert isinstance(result.data, dict)
    assert result.data.get("title") == "Test Page"
    assert result.data.get("content") == "Test content"
    assert result.error is None

    assert mock_notion_service.get_page.call_count == 1
    assert mock_notion_service.get_block_children.call_count == 1
    mock_notion_service.get_page.assert_called_with("test-page-id")
    mock_notion_service.get_block_children.assert_called_with("test-page-id")


async def test_read_page_tool_without_content(
    agent: NotionAgent, mock_notion_service: MagicMock
) -> None:
    """Test read page tool without content."""
    tool = agent.tools["read_page"]
    result = await tool.execute(
        page_id="test-page-id",
        include_content=False,
    )

    assert result.success is True
    assert isinstance(result.data, dict)
    assert result.data.get("title") == "Test Page"
    assert result.error is None

    assert mock_notion_service.get_page.call_count == 1
    assert mock_notion_service.get_block_children.call_count == 0
    mock_notion_service.get_page.assert_called_with("test-page-id")


async def test_edit_page_tool_title_only(
    agent: NotionAgent, mock_notion_service: MagicMock
) -> None:
    """Test edit page tool with title only."""
    tool = agent.tools["edit_page"]
    result = await tool.execute(
        page_id="test-page-id",
        title="Updated Title",
    )

    assert result.success is True
    assert isinstance(result.data, dict)
    assert result.data.get("title_updated") is True
    assert result.data.get("content_updated") is False
    assert result.error is None

    assert mock_notion_service.get_page.call_count == 1
    assert mock_notion_service.update_page.call_count == 1
    assert mock_notion_service.append_blocks.call_count == 0


async def test_edit_page_tool_content_replace(
    agent: NotionAgent, mock_notion_service: MagicMock
) -> None:
    """Test edit page tool with content replacement."""
    tool = agent.tools["edit_page"]
    result = await tool.execute(
        page_id="test-page-id",
        content="Updated content",
        append_content=False,
    )

    assert result.success is True
    assert isinstance(result.data, dict)
    assert result.data.get("content_updated") is True
    assert result.data.get("append_content") is False
    assert result.error is None

    assert mock_notion_service.get_page.call_count == 1
    assert mock_notion_service.get_block_children.call_count == 1
    assert mock_notion_service.update_block.call_count == 1
    assert mock_notion_service.append_blocks.call_count == 1


async def test_edit_page_tool_content_append(
    agent: NotionAgent, mock_notion_service: MagicMock
) -> None:
    """Test edit page tool with content append."""
    tool = agent.tools["edit_page"]
    result = await tool.execute(
        page_id="test-page-id",
        content="Additional content",
        append_content=True,
    )

    assert result.success is True
    assert isinstance(result.data, dict)
    assert result.data.get("content_updated") is True
    assert result.data.get("append_content") is True
    assert result.error is None

    assert mock_notion_service.get_page.call_count == 1
    assert mock_notion_service.get_block_children.call_count == 0
    assert mock_notion_service.update_block.call_count == 0
    assert mock_notion_service.append_blocks.call_count == 1


async def test_error_handling(
    agent: NotionAgent, mock_notion_service: MagicMock
) -> None:
    """Test error handling."""
    mock_notion_service.get_page.side_effect = Exception("Test error")
    tool = agent.tools["read_page"]
    result = await tool.execute(
        page_id="test-page-id",
        include_content=True,
    )

    assert result.success is False
    assert result.error == "Test error"
    assert result.data is None
