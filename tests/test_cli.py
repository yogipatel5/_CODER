"""Tests for the CLI interface."""

from unittest.mock import AsyncMock, MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from notion.agent.base import AgentResponse
from notion.cli.commands import cli, load_config
from notion.services import NotionConfig


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set up mock environment variables."""
    monkeypatch.setenv("NOTION_API_KEY", "test-api-key")
    monkeypatch.setenv("NOTION_BASE_URL", "https://test.notion.api")
    monkeypatch.setenv("NOTION_VERSION", "2022-06-28")


def test_load_config_with_env(mock_env: None) -> None:
    """Test loading configuration from environment variables."""
    config = load_config()
    assert isinstance(config, NotionConfig)
    assert config.api_key == "test-api-key"
    assert config.base_url == "https://test.notion.api"
    assert config.version == "2022-06-28"


def test_load_config_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading configuration without API key."""
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    with pytest.raises(click.UsageError):
        load_config()


@pytest.mark.asyncio
async def test_execute_command_success(cli_runner: CliRunner, mock_env: None) -> None:
    """Test successful execution of a command."""
    # Mock the agent's execute method
    mock_response = AgentResponse(
        success=True, data={"page_id": "test-page"}, metadata={"tool": "create_page"}
    )

    with (
        patch("notion.cli.commands.NotionAgent") as MockAgent,
        patch("notion.cli.commands.asyncio.run") as mock_run,
    ):
        # Configure the mocks
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(return_value=mock_response)
        MockAgent.return_value = mock_agent
        mock_run.return_value = mock_response

        # Run the command
        result = cli_runner.invoke(
            cli, ["execute", 'create page "Test Page": This is content']
        )

        # Verify the result
        assert result.exit_code == 0
        assert "Success!" in result.output
        assert "page_id" in result.output
        assert "create_page" in result.output


@pytest.mark.asyncio
async def test_execute_command_error(cli_runner: CliRunner, mock_env: None) -> None:
    """Test error handling in command execution."""
    # Mock the agent's execute method to return an error
    mock_response = AgentResponse(success=False, error="Invalid prompt format")

    with (
        patch("notion.cli.commands.NotionAgent") as MockAgent,
        patch("notion.cli.commands.asyncio.run") as mock_run,
    ):
        # Configure the mocks
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(return_value=mock_response)
        MockAgent.return_value = mock_agent
        mock_run.return_value = mock_response

        # Run the command
        result = cli_runner.invoke(cli, ["execute", "invalid prompt"])

        # Verify the result
        assert result.exit_code == 0  # Click handles the error
        assert "Error" in result.output
        assert "Invalid prompt format" in result.output


@pytest.mark.asyncio
async def test_execute_command_with_options(
    cli_runner: CliRunner, mock_env: None
) -> None:
    """Test command execution with custom options."""
    # Mock the agent's execute method
    mock_response = AgentResponse(success=True)

    with (
        patch("notion.cli.commands.NotionAgent") as MockAgent,
        patch("notion.cli.commands.asyncio.run") as mock_run,
    ):
        # Configure the mocks
        mock_agent = MagicMock()
        mock_agent.execute = AsyncMock(return_value=mock_response)
        MockAgent.return_value = mock_agent
        mock_run.return_value = mock_response

        # Run the command with options
        result = cli_runner.invoke(
            cli,
            ["execute", "--max-retries", "5", "--timeout", "60.0", "read page abc123"],
        )

        # Verify the result
        assert result.exit_code == 0
        assert "Success!" in result.output

        # Verify the options were passed correctly
        MockAgent.assert_called_once()
        config = MockAgent.call_args[0][0]
        assert config.max_retries == 5
        assert config.timeout == 60.0
