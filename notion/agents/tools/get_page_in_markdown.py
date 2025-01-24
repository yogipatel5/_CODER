import os
from typing import Any, Dict, List, Optional, Type

from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import Client
from pydantic import BaseModel, Field

load_dotenv()


class GetPageInMarkdownToolInput(BaseModel):
    """Input schema for getting page content in markdown."""

    page_id: str = Field(..., description="ID of the Notion page to convert to markdown")


class GetPageInMarkdownTool(BaseTool):
    name: str = "Get Page in Markdown"
    description: str = (
        "Retrieves a Notion page and converts its content to markdown format. "
        "This is the reverse operation of updating a page with markdown."
    )
    args_schema: Type[BaseModel] = GetPageInMarkdownToolInput

    def _convert_rich_text_to_markdown(self, rich_text: List[Dict[str, Any]]) -> str:
        """Convert Notion rich text to markdown format."""
        result = ""
        for text in rich_text:
            content = text.get("text", {}).get("content", "")
            annotations = text.get("annotations", {})
            link = text.get("text", {}).get("link")

            # Apply formatting based on annotations
            if annotations.get("code"):
                content = f"`{content}`"
            if annotations.get("bold"):
                content = f"**{content}**"
            if annotations.get("italic"):
                content = f"*{content}*"
            if annotations.get("strikethrough"):
                content = f"~~{content}~~"
            if link:
                content = f"[{content}]({link['url']})"

            result += content
        return result

    def _get_icon_content(self, icon: Optional[Dict[str, Any]]) -> str:
        """Extract icon content from a Notion icon object."""
        if not icon:
            return "💡"
        icon_type = icon.get("type")
        if icon_type == "emoji":
            return icon.get("emoji", "💡")
        elif icon_type == "external":
            return f"![icon]({icon['external']['url']})"
        elif icon_type == "file":
            return f"![icon]({icon['file']['url']})"
        return "💡"

    def _convert_block_to_markdown(self, block: Dict[str, Any], indent_level: int = 0) -> str:
        """Convert a Notion block to markdown format."""
        block_type = block.get("type", "")
        indent = "  " * indent_level
        content = ""

        if block_type == "paragraph":
            text = self._convert_rich_text_to_markdown(block["paragraph"]["rich_text"])
            content = f"{indent}{text}\n\n" if text else "\n"

        elif block_type == "heading_1":
            text = self._convert_rich_text_to_markdown(block["heading_1"]["rich_text"])
            content = f"{indent}# {text}\n\n"

        elif block_type == "heading_2":
            text = self._convert_rich_text_to_markdown(block["heading_2"]["rich_text"])
            content = f"{indent}## {text}\n\n"

        elif block_type == "heading_3":
            text = self._convert_rich_text_to_markdown(block["heading_3"]["rich_text"])
            content = f"{indent}### {text}\n\n"

        elif block_type == "bulleted_list_item":
            text = self._convert_rich_text_to_markdown(block["bulleted_list_item"]["rich_text"])
            content = f"{indent}- {text}\n"

        elif block_type == "numbered_list_item":
            text = self._convert_rich_text_to_markdown(block["numbered_list_item"]["rich_text"])
            content = f"{indent}1. {text}\n"

        elif block_type == "to_do":
            text = self._convert_rich_text_to_markdown(block["to_do"]["rich_text"])
            checked = block["to_do"]["checked"]
            checkbox = "[x]" if checked else "[ ]"
            content = f"{indent}- {checkbox} {text}\n"

        elif block_type == "code":
            text = self._convert_rich_text_to_markdown(block["code"]["rich_text"])
            language = block["code"]["language"]
            content = f"{indent}```{language}\n{text}\n```\n\n"

        elif block_type == "quote":
            text = self._convert_rich_text_to_markdown(block["quote"]["rich_text"])
            content = f"{indent}> {text}\n\n"

        elif block_type == "divider":
            content = f"{indent}---\n\n"

        elif block_type == "callout":
            text = self._convert_rich_text_to_markdown(block["callout"]["rich_text"])
            icon = block["callout"].get("icon")
            icon_content = self._get_icon_content(icon)
            content = f"{indent}> {icon_content} {text}\n\n"

        return content

    def _run(self, page_id: str) -> str:
        """
        Retrieve a Notion page and convert its content to markdown format.

        Args:
            page_id (str): The ID of the Notion page to convert

        Returns:
            str: The page content in markdown format
        """
        notion = Client(auth=os.getenv("NOTION_API_KEY"))

        # Get the page metadata
        page = notion.pages.retrieve(page_id)

        # Get the page icon and title
        icon = page.get("icon")
        icon_content = self._get_icon_content(icon)
        title = page.get("properties", {}).get("title", {}).get("title", [{}])[0].get("plain_text", "Untitled")

        # Start with icon (if exists) and title
        markdown_content = f"{icon_content} # {title}\n\n" if icon else f"# {title}\n\n"

        # Get all blocks (content)
        blocks = notion.blocks.children.list(page_id)

        # Convert each block to markdown
        for block in blocks["results"]:
            markdown_content += self._convert_block_to_markdown(block)

        return markdown_content


if __name__ == "__main__":
    # Test the tool with a sample page
    test_page_id = "1809167955c881e2aab9ffd4ae7ef82b"  # Replace with an actual page ID
    tool = GetPageInMarkdownTool()
    markdown = tool.run(test_page_id)
    print(markdown)
