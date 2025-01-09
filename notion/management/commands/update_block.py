"""
Command to update a Notion block.
"""

from .base import NotionBaseCommand


class Command(NotionBaseCommand):
    help = "Update a Notion block's content"

    def add_arguments(self, parser):
        parser.add_argument("block_id", help="ID of the block to update")
        parser.add_argument("--type", help="Block type (e.g., paragraph, heading_1, toggle)")
        parser.add_argument("--content", help="New content for the block")
        parser.add_argument(
            "--child-content",
            nargs="*",
            help="Content for child blocks (for toggle blocks). Format: type:content",
        )

    def handle(self, *args, **options):
        block_id = options["block_id"]
        block_type = options["type"]
        content = options["content"]
        child_content = options.get("child_content", [])

        try:
            if not block_type or not content:
                raise ValueError("Block type and content are required")

            # Format the block data according to Notion's API
            block_data = {
                "type": block_type,
                block_type: {"rich_text": [{"type": "text", "text": {"content": content}}]},
            }

            # Update the main block
            result = self.api.update_block(block_id, block_data)
            self.stdout.write(self.style.SUCCESS(f"Updated block: {content}"))

            # Handle child blocks for toggles
            if block_type == "toggle" and child_content:
                children = []
                for child in child_content:
                    try:
                        child_type, child_text = child.split(":", 1)
                        children.append(
                            {
                                "type": child_type,
                                child_type: {"rich_text": [{"type": "text", "text": {"content": child_text}}]},
                            }
                        )
                    except ValueError:
                        self.stderr.write(f"Invalid child content format: {child}")
                        continue

                if children:
                    self.api.create_block(block_id, children)
                    self.stdout.write(self.style.SUCCESS(f"Added {len(children)} child blocks"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error updating block: {e}"))
