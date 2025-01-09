"""
Command to get a Notion page.
"""

import json
from typing import Any, Dict, List

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Get a Notion page by ID"

    def add_arguments(self, parser):
        parser.add_argument("page_id", help="ID of the page to retrieve")
        parser.add_argument(
            "--include-content",
            action="store_true",
            help="Include page content/blocks",
        )
        parser.add_argument(
            "--raw",
            action="store_true",
            help="Show raw API response",
        )
        parser.add_argument(
            "--show-ids",
            action="store_true",
            help="Show block IDs in the output",
        )

    def get_parent_info(self, parent: Dict[str, Any]) -> Dict[str, Any]:
        """Get parent information including title for page parents."""
        parent_type = parent.get("type", "unknown")
        parent_info = {"type": parent_type, "id": None, "title": None}

        if parent_type == "workspace":
            parent_info["id"] = parent.get("workspace_id")
            parent_info["title"] = "Workspace"
        elif parent_type == "page_id":
            parent_id = parent.get("page_id")
            parent_info["id"] = parent_id
            try:
                if parent_id:
                    parent_page = self.api.get_page(parent_id)
                    parent_info["title"] = self.get_title_from_page(parent_page)
                else:
                    parent_info["title"] = "Unknown"
            except Exception:
                parent_info["title"] = "Unknown"
        elif parent_type == "database_id":
            parent_info["id"] = parent.get("database_id")
            parent_info["title"] = "Database"  # Could fetch database title if needed

        return parent_info

    def format_block_content(self, block: Dict[str, Any], show_ids: bool = False) -> List[Dict[str, Any]]:
        """Format a block's content for display."""
        block_type = block.get("type")
        if not block_type:
            return []

        # Get the content based on block type
        block_data = block.get(block_type, {})
        rich_text = block_data.get("rich_text", [])
        content = "".join(text.get("plain_text", "") for text in rich_text)

        # Format the block
        formatted = {
            "type": block_type,
            "content": content,
            "indent": block.get("indent", 0),
        }

        # Add special formatting for specific block types
        if block_type == "to_do":
            formatted["checked"] = block_data.get("checked", False)
        elif block_type == "code":
            formatted["content"] = content
            formatted["language"] = block_data.get("language", "plain text")
        elif block_type == "callout":
            icon = block_data.get("icon", {})
            if icon.get("type") == "emoji":
                formatted["content"] = f"{icon.get('emoji', '')} {content}"

        # Add block ID if requested
        if show_ids:
            formatted["id"] = block.get("id")

        # Handle child blocks if present
        if block.get("has_children"):
            child_blocks = self.api.get_block_children(block["id"])
            for child in child_blocks:
                formatted.setdefault("children", []).extend(self.format_block_content(child, show_ids))

        return [formatted]

    def handle(self, *args, **options):
        response = {
            "success": False,
            "message": "",
            "context": "",
            "data": {
                "page": None,
                "content": None,
            },
            "progress": [],
        }

        try:
            page_id = options["page_id"]
            include_content = options.get("include_content", False)
            raw = options.get("raw", False)
            show_ids = options.get("show_ids", False)

            # Get the page
            try:
                page = self.api.get_page(page_id)
            except Exception as e:
                response.update(
                    {
                        "message": f"Page not found: {page_id}",
                        "context": "Use 'list_pages' command to get valid page IDs",
                        "error": str(e),
                    }
                )
                self.stdout.write(json.dumps(response, indent=2))
                return

            # Format the response
            if raw:
                response["data"]["page"] = page
            else:
                parent_info = self.get_parent_info(page.get("parent", {}))
                response["data"]["page"] = {
                    "id": page["id"],
                    "title": self.get_title_from_page(page),
                    "url": page.get("url"),
                    "created_time": page.get("created_time"),
                    "last_edited_time": page.get("last_edited_time"),
                    "parent": parent_info,
                    "properties": page.get("properties"),
                }

            # Get content if requested
            if include_content:
                blocks = self.api.get_block_children(page_id)
                formatted_blocks = []
                for block in blocks:
                    formatted_blocks.extend(self.format_block_content(block, show_ids=show_ids))
                response["data"]["content"] = formatted_blocks
            else:
                response["context"] = "Add --include-content to view page blocks"

            # Add context about raw and show-ids options if not used
            if not raw and not show_ids:
                response["context"] = (
                    response["context"] + "\nAdd --raw to see raw API response, --show-ids to see block IDs"
                )

            response.update(
                {"success": True, "message": f"Successfully retrieved page: {self.get_title_from_page(page)}"}
            )

        except Exception as e:
            response.update({"message": "Error retrieving page", "error": str(e)})

        self.stdout.write(json.dumps(response, indent=2))
