import os
from typing import Type

from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import APIErrorCode, APIResponseError, Client
from pydantic import BaseModel, Field

load_dotenv()


class EditPageToolInput(BaseModel):
    """Input schema for editing a page in Notion."""

    page_id: str = Field(..., description="ID of the page to edit.")
    title: str = Field(None, description="New title of the page.")
    parent_id: str = Field(None, description="New ID of the parent page.")
    content_blocks: list = Field(
        default_factory=list, description="Optional content blocks to add to the page."
    )


class EditPageTool(BaseTool):
    name: str = "Edit Page Tool"
    description: str = (
        "Tool for editing a page in Notion by its ID. "
        "You can provide a new title, parent ID, and content blocks to add to the page."
    )
    args_schema: Type[BaseModel] = EditPageToolInput

    def _run(
        self,
        page_id: str,
        title: str = None,
        parent_id: str = None,
        content_blocks: list = None,
    ) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        properties = {}
        try:
            if title:
                properties["title"] = [{"text": {"content": title}}]
            if parent_id:
                notion.pages.update(
                    page_id, parent={"type": "page_id", "page_id": parent_id}
                )
            if properties:
                notion.pages.update(page_id, properties=properties)
            if content_blocks:
                for block in content_blocks:
                    notion.blocks.children.append(page_id, children=[block])

            return f"Page with ID '{page_id}' has been updated."
        except APIResponseError as error:
            if error.code == APIErrorCode.ObjectNotFound:
                return {"success": False, "error": "Page not found"}
            else:
                return {"success": False, "error": str(error)}


if __name__ == "__main__":
    tool = EditPageTool()
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
            page_id="17491679-55c8-8029-ab49-effe45a7b2ac",
            title="Updated Test Page",
            content_blocks=example_content_blocks,
        )
    )
