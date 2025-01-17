import os
from typing import Any, Dict, Type

from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import Client
from pydantic import BaseModel, Field

load_dotenv()


class ListPagesToolInput(BaseModel):
    """Input schema for ListPagesTool."""

    database_id: str = Field(
        ..., description="The ID of the database to list pages from."
    )


class ListPagesTool(BaseTool):
    name: str = "list_notion_pages"
    description: str = (
        "Lists pages from a specified Notion database, returning essential information "
        "including page ID, title, and URL. Useful for finding specific pages or "
        "getting an overview of database contents."
    )
    args_schema: Type[BaseModel] = ListPagesToolInput

    def _run(self, database_id: str) -> Dict[str, Any]:
        notion = Client(auth=os.getenv("NOTION_TOKEN"))

        response = notion.databases.query(
            database_id=database_id, page_size=100
        )  # Adjust as needed

        pages = []
        for page in response["results"]:
            # Extract the title from properties (assuming there's a title property)
            title = (
                page["properties"]
                .get("title", {})
                .get("title", [{}])[0]
                .get("plain_text", "Untitled")
            )

            page_info = {
                "id": page["id"],
                "title": title,
                "url": page["url"],
                "last_edited": page["last_edited_time"],
            }
            pages.append(page_info)

        return {"success": True, "data": {"pages": pages}}
