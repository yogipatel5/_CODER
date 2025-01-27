import os
import re
from typing import Type

from crewai.tools import BaseTool
from dotenv import load_dotenv
from notion_client import APIResponseError, Client
from pydantic import BaseModel, Field

load_dotenv()


class CreatePageWithMarkdownToolInput(BaseModel):
    """Input schema for creating a new Notion page with markdown content."""

    parent_id: str = Field(..., description="ID of the parent page or database where the new page will be created.")
    markdown_content: str = Field(..., description="Markdown content to upload.")
    title: str = Field(..., description="Required title for the page.")


class CreatePageWithMarkdownTool(BaseTool):
    name: str = "Create Page with Markdown Tool"
    description: str = (
        "Tool for creating a Notion page with markdown content. "
        "Converts markdown to Notion blocks and creates a new page."
    )
    args_schema: Type[BaseModel] = CreatePageWithMarkdownToolInput

    def _create_rich_text(self, content: str, annotations: dict = None) -> dict:
        """Create a properly formatted rich text object for Notion API."""
        if annotations is None:
            annotations = {
                "bold": False,
                "italic": False,
                "strikethrough": False,
                "underline": False,
                "code": False,
                "color": "default",
            }

        return {
            "type": "text",
            "text": {"content": content, "link": None},
            "annotations": annotations,
            "plain_text": content,
        }

    def _parse_inline_formatting(self, text: str) -> list:
        """Parse inline formatting like bold, italic, links, and images."""
        if not text:
            return [self._create_rich_text("")]

        segments = []
        current_pos = 0

        # Regular expressions for different inline elements
        patterns = {
            r"\*\*(.+?)\*\*": lambda m: self._create_rich_text(
                m.group(1),
                {
                    "bold": True,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default",
                },
            ),
            r"\*(.+?)\*": lambda m: self._create_rich_text(
                m.group(1),
                {
                    "bold": False,
                    "italic": True,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default",
                },
            ),
            r"\[(.+?)\]\((.+?)\)": lambda m: {
                "type": "text",
                "text": {"content": m.group(1), "link": {"url": m.group(2)}},
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default",
                },
                "plain_text": m.group(1),
            },
        }

        while current_pos < len(text):
            earliest_match = None
            earliest_pattern = None
            earliest_pos = len(text)

            for pattern in patterns:
                match = re.search(pattern, text[current_pos:])
                if match and match.start() + current_pos < earliest_pos:
                    earliest_match = match
                    earliest_pattern = pattern
                    earliest_pos = match.start() + current_pos

            if earliest_match:
                # Add text before the match
                if earliest_pos > current_pos:
                    segments.append(self._create_rich_text(text[current_pos:earliest_pos]))

                # Add the formatted segment
                segments.append(patterns[earliest_pattern](earliest_match))
                current_pos = earliest_pos + len(earliest_match.group(0))
            else:
                # Add remaining text
                if current_pos < len(text):
                    segments.append(self._create_rich_text(text[current_pos:]))
                break

        return segments if segments else [self._create_rich_text("")]

    def _get_list_indentation(self, line: str) -> int:
        """Get the indentation level of a list item."""
        return len(line) - len(line.lstrip())

    def _process_list_items(self, lines: list[str], start_index: int) -> tuple[list[dict], int]:
        """Process a list and its nested items, returning the list blocks and the next line index."""
        blocks = []
        current_indent = self._get_list_indentation(lines[start_index])
        i = start_index

        while i < len(lines):
            line = lines[i].rstrip()
            # print(f"Debug: Processing list line {i}: {line[:50]}...")

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check indentation level
            indent = self._get_list_indentation(line)
            stripped_line = line.lstrip()

            # Handle images in list items
            if "![" in stripped_line and "](" in stripped_line:
                # print("Debug: Found image in list item")
                image_block = self._convert_image_to_block(stripped_line)
                if image_block:
                    blocks.append(image_block)
                    i += 1
                    continue

            # If we're back to no indentation and it's not a list item, we're done
            if indent == 0 and not stripped_line.startswith(("- ", "1. ", "- [ ] ", "- [x] ")):
                # print(f"Debug: Exiting list at line {i}, found non-list content at base level")
                return blocks, i

            # If we're at a lower indentation than where we started, we're done with this list
            if indent < current_indent:
                # print(f"Debug: Exiting list at line {i} due to indentation change")
                return blocks, i

            # Check if we've hit a new section marker
            if stripped_line.startswith(("#", "```", ">")):
                # print(f"Debug: Exiting list at line {i} due to new section marker")
                return blocks, i

            line = stripped_line

            # Process list items...
            if line.startswith(("- [ ] ", "- [x] ")):
                # To-do item processing...
                checked = line.startswith("- [x] ")
                content = line[6:] if checked else line[6:]
                block = {
                    "object": "block",
                    "type": "to_do",
                    "to_do": {
                        "rich_text": self._parse_inline_formatting(content),
                        "checked": checked,
                    },
                }
                blocks.append(block)

            elif line.startswith("- "):
                # Bullet point processing...
                content = line[2:]
                block = {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": self._parse_inline_formatting(content),
                    },
                }
                blocks.append(block)

            elif re.match(r"^\d+\. ", line):
                # Numbered list processing...
                content = line[line.index(". ") + 2 :]
                block = {
                    "object": "block",
                    "type": "numbered_list_item",
                    "numbered_list_item": {
                        "rich_text": self._parse_inline_formatting(content),
                    },
                }
                blocks.append(block)

            else:
                # If we hit a non-list line, we're done
                # print(f"Debug: Exiting list at line {i} due to non-list content")
                return blocks, i

            # Check for nested content
            next_line = i + 1
            if next_line < len(lines):
                next_indent = self._get_list_indentation(lines[next_line])
                if next_indent > indent:
                    nested_blocks, next_i = self._process_list_items(lines, next_line)
                    if nested_blocks:
                        block["has_children"] = True
                        block["nested_blocks"] = nested_blocks
                    i = next_i - 1

            i += 1

        return blocks, i

    def _convert_image_to_block(self, line: str) -> dict:
        """Convert an image reference to a Notion image block."""
        image_match = re.search(r"!\[(.*?)\]\((.*?)\)", line)
        if not image_match:
            return None

        caption, url = image_match.groups()
        return {
            "object": "block",
            "type": "image",
            "image": {
                "type": "external",
                "external": {"url": url},
                "caption": [{"type": "text", "text": {"content": caption, "link": None}}] if caption else [],
            },
        }

    def _convert_markdown_to_blocks(self, markdown_content: str) -> list:
        """Convert markdown content to Notion blocks."""
        blocks = []
        code_block = False
        code_content = []
        code_language = ""

        lines = markdown_content.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            # print(f"Debug: Processing line {i}: {line[:50]}...")

            # Handle standalone image references
            if "![" in line and "](" in line and line.lstrip().startswith("!["):
                # print("Debug: Found standalone image reference")
                image_block = self._convert_image_to_block(line)
                if image_block:
                    blocks.append(image_block)
                    i += 1
                    continue

            # Skip empty lines unless in code block
            if not line and not code_block:
                # print("Debug: Skipping empty line")
                i += 1
                continue

            # Code blocks
            if line.startswith("```"):
                # print("Debug: Found code block marker")
                if not code_block:
                    code_block = True
                    code_language = line[3:] or "plain text"
                    code_content = []
                    # print(f"Debug: Starting code block with language: {code_language}")
                else:
                    # print("Debug: Ending code block")
                    blocks.append(
                        {
                            "object": "block",
                            "type": "code",
                            "code": {
                                "rich_text": [{"type": "text", "text": {"content": "\n".join(code_content)}}],
                                "language": code_language,
                            },
                        }
                    )
                    code_block = False
                i += 1
                continue

            if code_block:
                # print("Debug: Adding line to code block")
                code_content.append(line)
                i += 1
                continue

            # Headers with inline formatting (check these first)
            if line.startswith("# "):
                # print("Debug: Found H1 header")
                blocks.append(
                    {
                        "object": "block",
                        "type": "heading_1",
                        "heading_1": {"rich_text": self._parse_inline_formatting(line[2:])},
                    }
                )
                i += 1
                continue
            elif line.startswith("## "):
                # print("Debug: Found H2 header")
                blocks.append(
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {"rich_text": self._parse_inline_formatting(line[3:])},
                    }
                )
                i += 1
                continue
            elif line.startswith("### "):
                # print("Debug: Found H3 header")
                blocks.append(
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {"rich_text": self._parse_inline_formatting(line[4:])},
                    }
                )
                i += 1
                continue

            # Lists (bullet points, numbered lists, and tasks)
            if line.lstrip().startswith(("- ", "1. ", "- [ ] ", "- [x] ")):
                # print("Debug: Found list item")
                list_blocks, next_line = self._process_list_items(lines, i)
                # print(f"Debug: Processed {len(list_blocks)} list blocks")
                blocks.extend(list_blocks)
                i = next_line
                continue

            # Quotes
            elif line.startswith("> "):
                blocks.append(
                    {
                        "object": "block",
                        "type": "quote",
                        "quote": {"rich_text": self._parse_inline_formatting(line[2:])},
                    }
                )
                i += 1
                continue

            # Dividers
            elif line.startswith("---"):
                blocks.append({"object": "block", "type": "divider", "divider": {}})
                i += 1
                continue

            # Tables
            elif "|" in line:
                if i + 1 < len(lines) and all(c in "|-" for c in lines[i + 1]):
                    table_rows = []
                    header = [cell.strip() for cell in line.split("|")[1:-1]]
                    i += 2  # Skip the separator line

                    while i < len(lines) and "|" in lines[i]:
                        row = [cell.strip() for cell in lines[i].split("|")[1:-1]]
                        table_rows.append(row)
                        i += 1

                    blocks.append(
                        {
                            "object": "block",
                            "type": "table",
                            "table": {
                                "table_width": len(header),
                                "has_column_header": True,
                                "has_row_header": False,
                                "children": [
                                    {
                                        "object": "block",
                                        "type": "table_row",
                                        "table_row": {"cells": [[self._create_rich_text(cell)] for cell in row]},
                                    }
                                    for row in [header] + table_rows
                                ],
                            },
                        }
                    )
                    continue

            # Regular paragraphs with inline formatting (default case)
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": self._parse_inline_formatting(line)},
                }
            )
            i += 1

        return blocks

    def _run(
        self,
        parent_id: str,
        markdown_content: str,
        title: str,
    ) -> str:
        import asyncio

        notion = Client(auth=os.getenv("NOTION_API_KEY"))
        # print(f"Debug: Using Notion API key: {os.getenv('NOTION_API_KEY')[:4]}...")
        # print(f"Debug: Creating page under parent: {parent_id}")

        try:
            # Convert markdown to blocks
            blocks = self._convert_markdown_to_blocks(markdown_content)
            # print(f"Debug: Generated {len(blocks)} blocks")

            # Create the new page with title
            new_page = notion.pages.create(
                parent={"page_id": parent_id},
                properties={"title": {"title": [{"text": {"content": title}}]}},
            )
            page_id = new_page["id"]
            # print(f"Debug: Created new page with ID: {page_id}")

            async def process_block_with_children(blocks_to_process, parent_id):
                # Separate top-level blocks and their children
                top_level_blocks = []
                child_operations = []

                for block in blocks_to_process:
                    # Remove nested blocks from the main block
                    nested_blocks = block.pop("nested_blocks", None)
                    has_children = block.pop("has_children", False)

                    top_level_blocks.append(block)

                    if has_children and nested_blocks:
                        child_operations.append((nested_blocks, len(top_level_blocks) - 1))

                # Create all top-level blocks in one API call
                # print(f"Debug: Creating {len(top_level_blocks)} blocks")
                response = notion.blocks.children.append(parent_id, children=top_level_blocks)

                # Process nested blocks for each parent that has children
                for nested_blocks, parent_index in child_operations:
                    block_id = response["results"][parent_index]["id"]
                    await process_block_with_children(nested_blocks, block_id)

            # Process all blocks in one go
            asyncio.run(process_block_with_children(blocks, page_id))

            return f"Successfully created new page '{title}' with ID: {page_id}"

        except APIResponseError as error:
            # print(f"Debug: API Error Code: {error.code}")
            # print(f"Debug: API Error Body: {error.body}")
            # print(f"Debug: API Error Headers: {error.headers}")
            # print(f"Debug: API Error Status: {error.status}")
            return {"success": False, "error": f"Validation error: {error.body}"}
        except Exception as e:
            # print(f"Debug: Unexpected error: {str(e)}")
            return {"success": False, "error": f"Error creating page: {str(e)}"}

    def run(
        self,
        parent_id: str,
        markdown_content: str,
        title: str,
    ) -> str:
        return self._run(parent_id, markdown_content, title)
