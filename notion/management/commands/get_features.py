# This command is used by LLM to get features from Notion DB for this project.

import json
import logging

from django.core.management.base import BaseCommand

from notion.services.notion_project import ProjectNotionService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Get features from Notion DB"

    def handle(self, *args, **options):
        # Get Notion Project Page
        # project_page_id = "1769167955c8815f925ee2860e01f786"

        # Initialize Notion service
        notion_service = ProjectNotionService()

        # Get page content
        project_page_content = notion_service.get_project_page_content()
        logger.info(f"Retrieved {len(project_page_content)} blocks from page")

        # Print the page content details
        logger.info("Page Content Details:")
        logger.info(json.dumps(project_page_content, indent=2))

        logger.info("Command completed successfully")
