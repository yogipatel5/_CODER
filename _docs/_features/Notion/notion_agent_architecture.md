# Notion AI Agent Architecture

## Overview

An AI agent integrated into the existing `notion` package that processes natural language prompts to interact with Notion through the established service layer.

## System Structure

```
notion/
├── __init__.py          # Package exports
├── services.py          # Core Notion service
├── agent/              # AI Agent components
│   ├── __init__.py
│   ├── base.py         # Base agent implementation
│   ├── processor.py    # Prompt processing logic
│   └── tools/          # Tool implementations
│       ├── __init__.py
│       ├── create.py
│       ├── read.py
│       └── edit.py
├── cli/                # CLI components
│   ├── __init__.py
│   └── commands.py     # Click command implementations
└── config/            # Configuration
    ├── __init__.py
    └── settings.py    # Agent settings and constants

```

## Component Design

### 1. Agent Base (`notion/agent/base.py`)

```python
from typing import Dict, Any, List
from pydantic import BaseModel
from ..services import NotionService
from .tools import CreatePageTool, ReadPageTool, EditPageTool

class NotionAgent:
    """Base agent for Notion operations"""

    def __init__(self, service: NotionService):
        self.service = service
        self.tools = self._initialize_tools()

    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize available tools"""
        return {
            'create_page': CreatePageTool(self.service),
            'read_page': ReadPageTool(self.service),
            'edit_page': EditPageTool(self.service)
        }

    async def execute(self, prompt: str) -> Dict[str, Any]:
        """Execute a natural language prompt"""
        from .processor import PromptProcessor

        processor = PromptProcessor()
        action = processor.parse(prompt)
        tool = self.tools[action.tool_name]
        return await tool.execute(action.parameters)
```

### 2. Tools Implementation (`notion/agent/tools/`)

#### Base Tool (`notion/agent/tools/__init__.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel

class BaseTool(ABC):
    """Base class for all Notion tools"""

    def __init__(self, service):
        self.service = service

    @abstractmethod
    async def execute(self, params: BaseModel) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass

class ToolResult(BaseModel):
    """Standard tool result format"""
    success: bool
    data: Dict[str, Any]
    error: str = None
```

#### Create Tool (`notion/agent/tools/create.py`)

```python
from typing import Dict, Any
from pydantic import BaseModel
from . import BaseTool, ToolResult

class CreatePageParams(BaseModel):
    title: str
    content: str
    parent_id: str = None

class CreatePageTool(BaseTool):
    """Tool for creating Notion pages"""

    async def execute(self, params: CreatePageParams) -> ToolResult:
        try:
            page = await self.service.create_page(
                parent={"page_id": params.parent_id} if params.parent_id else None,
                properties={
                    "title": {"title": [{"text": {"content": params.title}}]}
                }
            )
            return ToolResult(success=True, data=page)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### 3. CLI Integration (`notion/cli/commands.py`)

```python
import click
from ..services import NotionService, NotionConfig
from ..agent.base import NotionAgent

@click.group()
def cli():
    """Notion AI Agent CLI"""
    pass

@cli.command()
@click.argument('prompt')
@click.option('--api-key', envvar='NOTION_API_KEY', required=True)
async def execute(prompt: str, api_key: str):
    """Execute a natural language prompt"""
    config = NotionConfig(api_key=api_key)
    service = NotionService(config)
    agent = NotionAgent(service)

    result = await agent.execute(prompt)
    click.echo(result)

def main():
    cli(auto_envvar_prefix='NOTION')
```

## Configuration (`notion/config/settings.py`)

```python
from pydantic import BaseSettings

class AgentSettings(BaseSettings):
    """Agent configuration settings"""
    model_name: str = "gpt-3.5-turbo"
    temperature: float = 0.7
    max_tokens: int = 150

    class Config:
        env_prefix = "NOTION_AGENT_"
```

## Integration with Existing Service

The agent leverages the existing `NotionService` implementation, using it as the foundation for all Notion operations. The tools act as specialized wrappers around the service methods, adding:

- Input validation
- Error handling
- Response formatting
- Logging and monitoring

## Usage Examples

1. Command Line:

```bash
# Direct usage
notion execute "Create a new page titled 'Meeting Notes'"

# With environment variables
export NOTION_API_KEY=your_key
notion execute "Read the page with ID abc123"
```

2. Programmatic Usage:

```python
from notion.services import NotionService, NotionConfig
from notion.agent.base import NotionAgent

# Initialize
config = NotionConfig(api_key="your_key")
service = NotionService(config)
agent = NotionAgent(service)

# Execute prompts
result = await agent.execute("Create a new page titled 'Test'")
```

## Implementation Phases

1. Phase 1: Core Integration (1 day)

   - Set up agent package structure
   - Implement base classes
   - Integrate with existing service

2. Phase 2: Tool Implementation (2 days)

   - Implement core tools
   - Add input validation
   - Set up error handling

3. Phase 3: CLI & Testing (1 day)
   - Implement CLI interface
   - Write unit tests
   - Add documentation

## Testing Strategy

```python
# tests/agent/test_base.py
import pytest
from notion.agent.base import NotionAgent
from notion.services import NotionService

@pytest.mark.asyncio
async def test_agent_execution():
    service = NotionService(config)
    agent = NotionAgent(service)

    result = await agent.execute(
        "Create a page titled 'Test'"
    )
    assert result.success
```

## Dependencies

```toml
[tool.poetry.dependencies]
notion-client = "^1.0.0"
pydantic = "^2.0.0"
click = "^8.0.0"
python-dotenv = "^1.0.0"
```
