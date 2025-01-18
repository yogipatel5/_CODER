import os
from typing import Type

from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import Client
from pydantic import BaseModel, Field

load_dotenv()


class DeletePageToolInput(BaseModel):
    """Input schema for deleting a page in Notion."""

    page_id: str = Field(..., description="ID of the page to delete.")


class DeletePageTool(BaseTool):
    name: str = "Delete Page Tool"
    description: str = "Tool for deleting a page in Notion by its ID."
    args_schema: Type[BaseModel] = DeletePageToolInput

    def _run(self, page_id: str) -> str:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        try:
            page = notion.pages.retrieve(page_id)
            if page.get("archived"):
                return f"Page with ID '{page_id}' is already deleted."

            title = page["properties"]["title"]["title"][0]["plain_text"]
            notion.pages.update(page_id, archived=True)
            return f"Page with Title: '{title}' and ID '{page_id}' has been deleted."

        except Exception as e:
            if "Could not find" in str(e):
                return f"Page with ID '{page_id}' does not exist or is already deleted."
            raise e


if __name__ == "__main__":
    tool = DeletePageTool()
    print(tool.run(page_id="17f91679-55c8-811b-9399-d6f00a8747ab"))
