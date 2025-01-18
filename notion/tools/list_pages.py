import os
from typing import Any, Dict

from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()


class ListPagesTool(BaseTool):
    name: str = "list_notion_pages"
    description: str = (
        "Lists all available pages from the Notion account, Page Title and ID, Child Pages will have a `parent` field."
    )

    def _run(self) -> Dict[str, Any]:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        response = notion.search(
            filter={"property": "object", "value": "page"},
            page_size=100,
        )

        pages = []
        for page in response["results"]:
            title = "Untitled"
            if "properties" in page and "title" in page["properties"]:
                title_items = page["properties"]["title"].get("title", [])
                if title_items:
                    title = title_items[0].get("plain_text", "Untitled")
            elif "title" in page:
                title_items = page.get("title", [])
                if title_items:
                    title = title_items[0].get("plain_text", "Untitled")

            page_info = {"id": page["id"], "title": title}

            if "parent" in page and page["parent"]:
                parent_type = page["parent"].get("type")
                if parent_type == "page_id":
                    page_info["parent"] = page["parent"]["page_id"]
                elif parent_type == "database_id":
                    page_info["parent"] = page["parent"]["database_id"]

            pages.append(page_info)

        return {"pages": pages}


if __name__ == "__main__":
    new_tool = ListPagesTool()
    print(new_tool.run())
