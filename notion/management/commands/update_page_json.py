"""
Command to update a Notion page using JSON input.
"""

import json
import sys
from typing import Any, Dict, List

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Update a Notion page using JSON input [page_id] [[--json-file] || [--json-string],[--verbose]], --help"

    def add_arguments(self, parser):
        parser.add_argument("page_id", help="ID of the page to update")
        parser.add_argument(
            "--json-file",
            help="Path to JSON file containing the update data",
        )
        parser.add_argument(
            "--json-string",
            help="JSON string containing the update data",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed progress",
        )

    def create_block_data(self, block: Dict[str, Any]) -> Dict[str, Any]:
        """Create the block data structure for the API."""
        # If the block is already in the correct format (has 'object' field), return as is
        if "object" in block and block["object"] == "block":
            return block

        block_type = block["type"]

        if block_type == "divider":
            return {"type": block_type, block_type: {}}

        if block_type == "callout":
            return {
                "type": block_type,
                block_type: {
                    "rich_text": [{"type": "text", "text": {"content": block["content"]}}],
                    "icon": {"type": "emoji", "emoji": block.get("icon", "💡")},
                },
            }

        if block_type == "to_do":
            return {
                "type": block_type,
                block_type: {
                    "rich_text": [{"type": "text", "text": {"content": block["content"]}}],
                    "checked": block.get("checked", False),
                },
            }

        return {
            "type": block_type,
            block_type: {"rich_text": [{"type": "text", "text": {"content": block["content"]}}]},
        }

    def update_blocks(self, page_id: str, blocks: List[Dict[str, Any]], verbose: bool = False) -> List[str]:
        """Update the blocks of a page. Returns a list of progress messages."""
        progress = []
        # First, get existing blocks to track what needs to be deleted
        existing_blocks = self.api.get_block_children(page_id)
        existing_ids = {block["id"] for block in existing_blocks}
        processed_ids = set()

        # Create/update blocks
        for block in blocks:
            block_id = block.get("id")
            block_data = self.create_block_data(block)

            if block_id and block_id in existing_ids:
                # Update existing block
                self.api.update_block(block_id, block_data)
                processed_ids.add(block_id)
                if verbose:
                    progress.append(f"Updated block: {block_id} ({block['type']})")

                # Handle children if present
                if block.get("children"):
                    child_progress = self.update_blocks(block_id, block["children"], verbose)
                    progress.extend(child_progress)
            else:
                # Create new block
                result = self.api.create_block(page_id, [block_data])
                new_block_id = result["results"][0]["id"]
                if verbose:
                    progress.append(f"Created block: {new_block_id} ({block['type']})")

                # Handle children if present
                if block.get("children"):
                    child_progress = self.update_blocks(new_block_id, block["children"], verbose)
                    progress.extend(child_progress)

        # Delete blocks that weren't processed
        for block_id in existing_ids - processed_ids:
            self.api.delete_block(block_id)
            if verbose:
                progress.append(f"Deleted block: {block_id}")

        return progress

    def handle(self, *args, **options):
        response = {"success": False, "message": "", "context": "", "data": None, "progress": []}

        try:
            page_id = options["page_id"]
            json_file = options.get("json_file")
            json_string = options.get("json_string")
            verbose = options.get("verbose", False)

            # Verify the page exists
            try:
                page = self.api.get_page(page_id)
                if verbose:
                    response["progress"].append(f"Found page: {self.get_title_from_page(page)} ({page_id})")
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

            # Get JSON data
            try:
                if json_file:
                    with open(json_file) as f:
                        data = json.load(f)
                elif json_string:
                    data = json.loads(json_string)
                elif not sys.stdin.isatty():
                    # Read from stdin if available
                    data = json.load(sys.stdin)
                else:
                    raise ValueError("Must provide either --json-file, --json-string, or pipe JSON data")
            except json.JSONDecodeError as e:
                response.update(
                    {
                        "message": "Invalid JSON data",
                        "error": str(e),
                        "context": """
Expected JSON format:
{
    "properties": {                    # Optional: Page properties to update
        "title": "Page Title",
        "status": "In Progress",
        ...
    },
    "content": [                      # Optional: Page content/blocks to update
        {
            "object": "block",        # Required for pre-formatted blocks
            "type": "paragraph",      # Block type (paragraph, heading_1, etc.)
            "paragraph": {            # Block type specific content
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": "Text content"
                    }
                }]
            }
        },
        ...
    ]
}""",
                    }
                )
                self.stdout.write(json.dumps(response, indent=2))
                return
            except Exception as e:
                response.update({"message": "Error reading JSON data", "error": str(e)})
                self.stdout.write(json.dumps(response, indent=2))
                return

            # Validate JSON structure
            if not isinstance(data, dict):
                response.update(
                    {
                        "message": "Invalid JSON structure",
                        "error": "Root element must be an object",
                        "context": "JSON must contain either 'properties' or 'content' or both",
                    }
                )
                self.stdout.write(json.dumps(response, indent=2))
                return

            if not any(key in data for key in ["properties", "content"]):
                response.update(
                    {
                        "message": "Invalid JSON structure",
                        "error": "Missing required keys",
                        "context": "JSON must contain either 'properties' or 'content' or both",
                    }
                )
                self.stdout.write(json.dumps(response, indent=2))
                return

            # Update properties if present
            if "properties" in data:
                properties = {}
                for key, value in data["properties"].items():
                    if key == "title":
                        properties[key] = {"title": [{"text": {"content": value}}]}
                    else:
                        properties[key] = {"rich_text": [{"text": {"content": value}}]}

                try:
                    self.api.update_page(page_id, properties)
                    if verbose:
                        response["progress"].append("Updated page properties")
                except Exception as e:
                    response.update(
                        {
                            "message": "Error updating properties",
                            "error": str(e),
                            "context": "Check if the property names are valid for this page",
                        }
                    )
                    self.stdout.write(json.dumps(response, indent=2))
                    return

            # Update content if present
            if "content" in data:
                try:
                    # Delete all existing blocks first
                    existing_blocks = self.api.get_block_children(page_id)
                    for block in existing_blocks:
                        self.api.delete_block(block["id"])
                        if verbose:
                            response["progress"].append(f"Deleted block: {block['id']}")

                    # Create new blocks in batches of 100 (Notion API limit)
                    batch_size = 100
                    for i in range(0, len(data["content"]), batch_size):
                        batch = data["content"][i : i + batch_size]
                        result = self.api.create_block(page_id, batch)
                        if verbose:
                            for block in result["results"]:
                                response["progress"].append(f"Created block: {block['id']} ({block['type']})")

                    if verbose:
                        response["progress"].append("Updated page content")
                except Exception as e:
                    response.update(
                        {
                            "message": "Error updating content",
                            "error": str(e),
                            "context": "Check if the block types and content format are valid",
                        }
                    )
                    self.stdout.write(json.dumps(response, indent=2))
                    return

            # Get the updated page to show the result
            updated_page = self.api.get_page(page_id)
            response.update(
                {
                    "success": True,
                    "message": f"Successfully updated page: {self.get_title_from_page(updated_page)}",
                    "data": {
                        "page_id": page_id,
                        "title": self.get_title_from_page(updated_page),
                        "url": updated_page.get("url"),
                    },
                }
            )

        except Exception as e:
            response.update(
                {
                    "message": "Error updating page",
                    "error": str(e),
                    "context": "Check the command help for usage details: python manage.py help notion update_page_json",
                }
            )

        self.stdout.write(json.dumps(response, indent=2))
