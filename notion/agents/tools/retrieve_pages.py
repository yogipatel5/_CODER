import os
from typing import Any, Dict, Optional

from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import Client

load_dotenv()


class RetrievePagesTool(BaseTool):
    name: str = "retrieve_notion_pages"
    description: str = (
        "Retrieves all available pages from the Notion account, "
        "Page Title and ID, Child Pages will have a `parent` field. "
        "If parent_id is provided, only returns pages under that parent."
    )

    def _get_page_title(self, page: Dict[str, Any]) -> str:
        """Extract title from a page object."""
        title = "Untitled"
        if "properties" in page and "title" in page["properties"]:
            title_items = page["properties"]["title"].get("title", [])
            if title_items:
                title = title_items[0].get("plain_text", "Untitled")
        elif "title" in page:
            title_items = page.get("title", [])
            if title_items:
                title = title_items[0].get("plain_text", "Untitled")
        return title

    def _get_page_info(self, page: Dict[str, Any], is_child: bool = False) -> Dict[str, Any]:
        """Convert a page object to page info dict."""
        if is_child:
            # For child pages from blocks API
            return {"id": page["id"], "title": page.get("child_page", {}).get("title", "Untitled"), "is_child": True}

        # For pages from search API
        page_info = {"id": page["id"], "title": self._get_page_title(page), "is_child": False}

        if "parent" in page and page["parent"]:
            parent_type = page["parent"].get("type")
            if parent_type == "page_id":
                page_info["parent"] = page["parent"]["page_id"]
            elif parent_type == "database_id":
                page_info["parent"] = page["parent"]["database_id"]

        return page_info

    def _run(self, parent_id: Optional[str] = None) -> Dict[str, Any]:
        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        pages = []

        if parent_id:
            # Get direct child pages using blocks API
            children = notion.blocks.children.list(parent_id)
            for block in children["results"]:
                if block["type"] == "child_page":
                    pages.append(self._get_page_info(block, is_child=True))
        else:
            # Get all pages using search API
            response = notion.search(
                filter={"property": "object", "value": "page"},
                page_size=100,
            )

            for page in response["results"]:
                pages.append(self._get_page_info(page))

        return {"pages": pages, "total": len(pages), "parent_id": parent_id}


if __name__ == "__main__":
    new_tool = RetrievePagesTool()
    print(new_tool.run())
