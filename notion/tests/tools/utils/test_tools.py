"""
Test tool implementations for testing.
"""

from typing import Any, ClassVar, Dict, Type

from pydantic import BaseModel, Field

from notion.tools.base import NotionBaseTool


class TestToolArgs(BaseModel):
    """Test tool arguments."""

    pass


class TestNotionTool(NotionBaseTool):
    """Concrete implementation for testing."""

    name: ClassVar[str] = "test_tool"
    description: ClassVar[str] = "Test tool for unit testing"
    args_schema: ClassVar[Type[BaseModel]] = TestToolArgs

    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """Test implementation."""
        return self._format_response(success=True, message="Test run")
