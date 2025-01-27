import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MarkdownService:
    """Service for converting Notion blocks to markdown and vice versa."""

    def __init__(self):
        pass

    def convert_blocks_to_markdown(self, blocks: List[Dict[str, Any]]) -> str:
        """Convert a list of Notion blocks to markdown format."""
        if not blocks:
            return ""

        markdown = ""
        for block in blocks:
            logger.debug("Converting block type: %s", block.get("type"))
            markdown += self._convert_block_to_markdown(block)
        return markdown.strip()

    def _convert_block_to_markdown(self, block: Dict[str, Any], indent: str = "") -> str:
        """Convert a single Notion block to markdown format."""
        block_type = block.get("type")
        if not block_type:
            logger.warning("Block missing type: %s", block)
            return ""

        logger.debug("Processing block type: %s", block_type)
        try:
            content = ""

            # Handle headings without indentation
            if block_type in ["heading_1", "heading_2", "heading_3"]:
                text = self._convert_rich_text_to_markdown(block[block_type]["rich_text"])
                level = int(block_type[-1])  # Get the heading level from the type
                content = "#" * level + " " + text + "\n\n"

            # Handle other block types with proper indentation
            elif block_type == "paragraph":
                text = self._convert_rich_text_to_markdown(block["paragraph"]["rich_text"])
                content = f"{indent}{text}\n\n" if text else "\n"

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
                content = f"{indent}```{language}\n{text}\n{indent}```\n\n"

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

            elif block_type == "child_database":
                title = block["child_database"].get("title", "Untitled Database")
                content = f"{indent}### {title} (Database)\n\n"

            elif block_type == "table":
                content = self._convert_table_to_markdown(block["table"], indent)

            elif block_type == "column_list":
                # Don't add indentation for column lists
                for column in block.get("children", []):
                    content += self._convert_block_to_markdown(column, indent)

            elif block_type == "column":
                # Process column contents with current indentation
                for child in block.get("children", []):
                    content += self._convert_block_to_markdown(child, indent)

            elif block_type == "image":
                image_block = block["image"]
                caption = self._convert_rich_text_to_markdown(image_block.get("caption", []))
                url = image_block.get("file", {}).get("url", "") or image_block.get("external", {}).get("url", "")
                alt_text = caption or "image"
                content = f"{indent}![{alt_text}]({url})\n\n"

            else:
                logger.warning("Unsupported block type encountered: %s", block_type)
                content = f"{indent}> ⚠️ Unsupported block type: {block_type}\n\n"

            # Handle children blocks if they exist
            # Only indent children for certain block types
            if block.get("has_children") and "children" in block:
                child_indent = (
                    indent + "  "
                    if block_type in ["bulleted_list_item", "numbered_list_item", "to_do", "quote", "callout"]
                    else indent
                )

                for child in block["children"]:
                    content += self._convert_block_to_markdown(child, child_indent)

            return content

        except Exception as e:
            logger.error("Error converting block type %s: %s", block_type, str(e))
            return f"{indent}> ⚠️ Error converting {block_type}: {str(e)}\n\n"

    def _convert_table_to_markdown(self, table: Dict[str, Any], indent: str = "") -> str:
        """Convert a Notion table to markdown format."""
        if not table.get("rows"):
            return ""

        content = []
        header = ["Column " + str(i + 1) for i in range(table.get("table_width", 0))]
        content.append("| " + " | ".join(header) + " |")
        content.append("| " + " | ".join(["---"] * len(header)) + " |")

        for row in table.get("rows", []):
            cells = []
            for cell in row.get("cells", []):
                cell_text = self._convert_rich_text_to_markdown(cell)
                cells.append(cell_text or " ")
            content.append("| " + " | ".join(cells) + " |")

        return indent + "\n".join(content) + "\n\n"

    def _convert_rich_text_to_markdown(self, rich_text: List[Dict[str, Any]]) -> str:
        """Convert Notion rich text to markdown format."""
        if not rich_text:
            return ""

        result = ""
        for text in rich_text:
            content = text.get("text", {}).get("content", "")
            annotations = text.get("annotations", {})

            # Apply text formatting
            if annotations.get("bold"):
                content = f"**{content}**"
            if annotations.get("italic"):
                content = f"*{content}*"
            if annotations.get("strikethrough"):
                content = f"~~{content}~~"
            if annotations.get("code"):
                content = f"`{content}`"
            if annotations.get("underline"):
                content = f"__{content}__"

            # Handle links
            if text.get("href"):
                content = f"[{content}]({text['href']})"

            result += content

        return result

    def _get_icon_content(self, icon: Optional[Dict[str, Any]]) -> str:
        """Convert a Notion icon to markdown format."""
        if not icon:
            return ""

        icon_type = icon.get("type")
        if icon_type == "emoji":
            return icon.get("emoji", "")
        elif icon_type == "external":
            return f"![icon]({icon['external']['url']})"
        elif icon_type == "file":
            return f"![icon]({icon['file']['url']})"
        return ""

    def convert_markdown_to_blocks(self, markdown: str) -> List[Dict[str, Any]]:
        """Convert markdown to Notion blocks. To be implemented."""
        # TODO: Implement markdown to blocks conversion
        pass
