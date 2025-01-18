import os
from typing import Type

from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import Client
from pydantic import BaseModel, Field

load_dotenv()


class CreatePageToolInput(BaseModel):
    """Input schema for creating a page in Notion."""

    title: str = Field(..., description="Title of the page to create.")
    parent_id: str = Field(..., description="ID of the parent page.")
    content_blocks: list = Field(
        default_factory=list, description="Optional content blocks to add to the page."
    )


class CreatePageTool(BaseTool):
    name: str = "Create Page Tool"
    description: str = (
        "Tool for creating a new page in Notion with a specified title and parent. "
        "Optionally, you can provide content blocks to add to the page."
    )
    args_schema: Type[BaseModel] = CreatePageToolInput

    def _run(self, title: str, parent_id: str, content_blocks: list = None) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        properties = {"title": [{"text": {"content": title}}]}
        children = content_blocks if content_blocks else []
        response = notion.pages.create(
            parent={"type": "page_id", "page_id": parent_id},
            properties=properties,
            children=children,
        )

        return f"Page '{title}' Id: {response['id']} created under parent ID '{parent_id}'."


if __name__ == "__main__":
    tool = CreatePageTool()
    example_content_blocks = [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "text": [
                    {
                        "type": "text",
                        "text": {"content": "This is an example paragraph block."},
                    }
                ]
            },
        }
    ]
    print(
        tool.run(
            title="Test Page with Content Blocks",
            parent_id="17491679-55c8-8029-ab49-effe45a7b2ac",
            content_blocks=example_content_blocks,
        )
    )
