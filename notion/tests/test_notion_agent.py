"""Tests for Notion agent functionality."""

import os
from unittest.mock import MagicMock, patch

import pytest
from crewai import Agent

from notion.crew import get_notion_agent


@pytest.fixture
def mock_notion_client():
    """Mock the Notion client."""
    with patch("notion_client.Client") as mock:
        # Mock search results
        mock.return_value.search.return_value = {
            "results": [
                {
                    "id": "test-page-id",
                    "properties": {"title": {"title": [{"plain_text": "Test Page"}]}},
                    "parent": {"type": "workspace", "id": "workspace"},
                    "url": "https://notion.so/test-page",
                    "created_time": "2024-01-01T00:00:00.000Z",
                    "last_edited_time": "2024-01-02T00:00:00.000Z",
                }
            ]
        }
        yield mock


def test_notion_agent_creation():
    """Test that we can create a Notion agent."""
    agent = get_notion_agent()
    assert isinstance(agent, Agent)
    assert agent.role == "Notion Workspace Manager"
    assert len(agent.tools) > 0
    assert any(tool.name == "list_notion_pages" for tool in agent.tools)


@pytest.mark.usefixtures("mock_notion_client")
def test_notion_agent_list_pages():
    """Test that the agent can list pages."""
    agent = get_notion_agent()

    # Find the list_pages tool
    list_pages_tool = next(tool for tool in agent.tools if tool.name == "list_notion_pages")

    # Use the tool
    result = list_pages_tool.run()

    assert result["success"] is True
    assert len(result["data"]["pages"]) == 1
    assert result["data"]["pages"][0]["title"] == "Test Page"


def test_notion_agent_config_override():
    """Test that we can override agent configuration."""
    custom_backstory = "Custom backstory for testing"
    agent = get_notion_agent(backstory=custom_backstory)

    assert agent.backstory == custom_backstory
