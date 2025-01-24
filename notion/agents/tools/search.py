import os
from typing import Type

import yaml
from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import APIResponseError, Client
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# Load project config if exists
try:
    with open("project.yaml", "r") as f:
        project_config = yaml.safe_load(f)

    # Set environment variables from project.yaml
    for key, value in project_config.get("env", {}).items():
        os.environ[key] = str(value)
except FileNotFoundError:
    project_config = {}

api_key = os.getenv("NOTION_API_KEY")
print(f"Debug: API Key loaded: {'Yes' if api_key else 'No'}")
print(f"Debug: API Key length: {len(api_key) if api_key else 0}")
print(f"Debug: Project config loaded: {'Yes' if project_config else 'No'}")


class SearchPagesToolInput(BaseModel):
    """Input schema for searching Notion pages."""

    search_term: str = Field(..., description="The search term to look for in Notion pages.")


class SearchPagesTool(BaseTool):
    name: str = "Search Pages Tool"
    description: str = "Tool for searching Notion pages. " "Returns a list of pages that match the search query."
    args_schema: Type[BaseModel] = SearchPagesToolInput

    def _run(self, search_term: str) -> str:
        notion = Client(auth=api_key)  # Use the globally loaded API key

        try:
            print(f"Debug: Searching for term: {search_term}")
            # First get all pages (without query to get everything)
            search_results = notion.search(filter={"value": "page", "property": "object"})
            pages = search_results.get("results", [])
            print(f"Debug: Found {len(pages)} total pages")

            matching_pages = []
            for page in pages:
                page_id = page.get("id")
                # Get blocks in the page
                blocks = notion.blocks.children.list(block_id=page_id).get("results", [])

                # Look for blocks containing the search term
                for block in blocks:
                    if block.get("type") == "paragraph":
                        rich_text = block.get("paragraph", {}).get("rich_text", [])
                        if rich_text and search_term in rich_text[0].get("text", {}).get("content", ""):
                            print(f"Debug: Found matching block in page: {page_id}")
                            print(f"Debug: URL: https://notion.so/{page_id.replace('-', '')}")
                            matching_pages.append(page)
                            break  # Found a match in this page, move to next page

            print(f"Debug: Found {len(matching_pages)} pages with matching content")
            return {"success": True, "results": matching_pages}
        except APIResponseError as error:
            print(f"Debug: API Error Code: {error.code}")
            print(f"Debug: API Error Body: {error.body}")
            print(f"Debug: API Error Headers: {error.headers}")
            print(f"Debug: API Error Status: {error.status}")
            return {"success": False, "error": f"Validation error: {error.body}"}
        except AttributeError as e:
            print(f"Debug: Unexpected error: {str(e)}")
            return {"success": False, "error": f"Error searching pages: {str(e)}"}


if __name__ == "__main__":
    search_term = "Notey"
    tool = SearchPagesTool()
    result = tool.run(search_term=search_term)
    print(result)
