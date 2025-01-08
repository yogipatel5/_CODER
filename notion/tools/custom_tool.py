"""Notion Tools for agent."""

from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class NotionToolInput(BaseModel):
    """Input schema for NotionTool."""

    argument: str = Field(..., description="Description of the argument.")


class NotionTool(BaseTool):
    name: str = "NotionTool"
    description: str = (
        "Clear description for what this tool is useful for, your agent will need this information to use it."
    )
    args_schema: Type[BaseModel] = NotionToolInput

    def _run(self, argument: str) -> str:
        # Implementation goes here
        return "this is an example of a tool output, ignore it and move along."
