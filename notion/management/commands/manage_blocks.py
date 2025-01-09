"""
Command to manage Notion blocks (create, update, delete).
"""

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Manage Notion blocks - create, update, or delete blocks"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["create", "update", "delete"], help="Action to perform")
        parser.add_argument("parent_id", help="ID of the parent page/block")
        parser.add_argument("--block-id", help="Block ID (required for update/delete)")
        parser.add_argument("--type", help="Block type (e.g., paragraph, heading_1)")
        parser.add_argument("--content", help="Block content")
        parser.add_argument(
            "--children",
            nargs="*",
            help="Child blocks in format type:content (for toggle blocks)",
        )

    def create_block_data(self, block_type: str, content: str) -> dict:
        """Create the block data structure for the API."""
        if block_type == "divider":
            return {"type": block_type, block_type: {}}

        if block_type == "callout":
            icon, content = content.split(" ", 1) if " " in content else ("💡", content)
            return {
                "type": block_type,
                block_type: {
                    "rich_text": [{"type": "text", "text": {"content": content}}],
                    "icon": {"type": "emoji", "emoji": icon},
                },
            }

        return {
            "type": block_type,
            block_type: {"rich_text": [{"type": "text", "text": {"content": content}}]},
        }

    def handle(self, *args, **options):
        action = options["action"]
        parent_id = options["parent_id"]
        block_id = options.get("block_id")
        block_type = options.get("type")
        content = options.get("content")
        children = options.get("children", [])

        try:
            if action == "create":
                if not block_type:
                    raise ValueError("Block type is required for create action")

                # Create the main block
                block_data = self.create_block_data(block_type, content or "")

                # Add children if this is a toggle block
                if block_type == "toggle" and children:
                    child_blocks = []
                    for child in children:
                        child_type, child_content = child.split(":", 1)
                        child_blocks.append(self.create_block_data(child_type, child_content))

                    # Create the toggle block first
                    result = self.api.create_block(parent_id, [block_data])
                    toggle_id = result["results"][0]["id"]

                    # Then add its children
                    self.api.create_block(toggle_id, child_blocks)
                    self.stdout.write(self.style.SUCCESS(f"Created toggle block with {len(child_blocks)} children"))
                else:
                    # Create a regular block
                    result = self.api.create_block(parent_id, [block_data])
                    self.stdout.write(self.style.SUCCESS("Created new block"))

            elif action == "update":
                if not block_id or not block_type:
                    raise ValueError("Block ID and type are required for update action")

                block_data = self.create_block_data(block_type, content or "")
                self.api.update_block(block_id, block_data)
                self.stdout.write(self.style.SUCCESS("Updated block"))

            elif action == "delete":
                if not block_id:
                    raise ValueError("Block ID is required for delete action")

                self.api.delete_block(block_id)
                self.stdout.write(self.style.SUCCESS("Deleted block"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error managing block: {e}"))
