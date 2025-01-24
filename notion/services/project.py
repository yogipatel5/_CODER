"""Service for interacting with Notion API to get project details."""
import logging
from typing import Dict, List

import yaml
from django.conf import settings

from notion.api.client import NotionClient

logger = logging.getLogger(__name__)


class ProjectNotionService:
    """Service class for handling Notion API interactions."""

    def __init__(self):
        """Initialize Notion client."""
        logger.debug("Initializing ProjectNotionService")
        self.client = NotionClient()

        with open(settings.BASE_DIR / "project.yaml", "r") as f:
            project_config = yaml.safe_load(f)
        notion_config = project_config.get("notion", {})
        self.project_page_id = notion_config.get("project_page_id")
        self.project_page_url = notion_config.get("project_page_url")

    def get_project_page_content(self) -> Dict:
        """
        Get the full content of a Notion page including all its blocks.

        Returns:
            Dict: Full page content including blocks
        """
        logger.debug(f"Fetching project page {self.project_page_id} from Notion API")
        return self.client.get_page(self.project_page_id)

    def get_project_page_blocks(self) -> List[Dict]:
        """
        Get all blocks from a Notion page.

        Returns:
            List[Dict]: List of block dictionaries
        """
        logger.debug(f"Fetching blocks for project page {self.project_page_id}")
        return self.client.get_block_children(self.project_page_id)
