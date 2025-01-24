"""Service for interacting with Notion API."""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from django.utils import timezone

from notion.api.client import NotionClient
from notion.models.notionagentjobs import NotionAgentJob

logger = logging.getLogger(__name__)


class NoteyService:
    """Service class for handling Notion API interactions."""

    def __init__(self):
        """Initialize Notion client."""
        logger.debug("Initializing NotionService with API key")
        self.client = NotionClient()

    def get_page(self, page_id: str) -> Dict:
        """
        Get the full content of a Notion page including all its blocks.

        Returns:
            Dict: Full page content including blocks
        """
        logger.debug(f"Fetching page {page_id} from Notion API")
        return self.client.get_page(page_id)

    def get_recent_pages(self) -> List[Dict]:
        """
        Fetch all pages from Notion, sorted by last edited time.

        Returns:
            List[Dict]: List of page objects from Notion API
        """
        logger.debug("Fetching recent pages from Notion API")
        pages = self.client.search_pages("")
        logger.debug(f"Retrieved {len(pages)} pages from Notion API")
        logger.info(f"Found {len(pages)} total pages")
        return pages

    def get_page_content(self, page_id: str) -> Dict:
        """
        Get the full content of a page including all its blocks.

        Args:
            page_id (str): Notion page ID

        Returns:
            Dict: Full page content including blocks
        """
        logger.debug(f"Fetching full content for page {page_id}")
        blocks = self.client.get_block_children(page_id)
        logger.debug(f"Retrieved {len(blocks)} blocks from page {page_id}")
        return blocks

    def has_notey_content(self, blocks: List[Dict]) -> Optional[str]:
        """
        Check if any block contains 'Notey' and extract its content.

        Args:
            blocks (List[Dict]): List of blocks from the page

        Returns:
            Optional[str]: The Notey task text if found, None otherwise
        """
        logger.debug(f"Searching through {len(blocks)} blocks for Notey content")

        for block in blocks:
            block_type = block.get("type")
            block_id = block.get("id")
            logger.debug(f"Checking block {block_id} of type {block_type}")

            # Get text content based on block type
            text_content = []
            if block_type == "paragraph":
                text_content = block.get("paragraph", {}).get("rich_text", [])
            elif block_type == "callout":
                text_content = block.get("callout", {}).get("rich_text", [])
                logger.debug(f"Found callout block with {len(text_content)} text segments")
                logger.debug(f"Callout icon: {block.get('callout', {}).get('icon', {})}")

            if not text_content:
                logger.debug(f"No text content found in block {block_id}")
                continue

            # Combine all text segments
            full_text = " ".join(segment.get("plain_text", "") for segment in text_content if segment.get("plain_text"))

            logger.debug(f"Block {block_id} text content: {full_text[:200]}")

            if "Notey" in full_text:
                # Clean up the text - remove any trailing whitespace or newlines
                full_text = full_text.strip()
                logger.debug(f"Found Notey content: {full_text}")
                return full_text

        logger.debug("No Notey content found")
        return None

    def create_agent_job(
        self, page_id: str, parent_page_id: Optional[str], last_edited: datetime, description: str, task_details: str
    ) -> NotionAgentJob:
        """
        Create a new NotionAgentJob for a Notey block.

        Args:
            page_id (str): Notion page ID
            parent_page_id (Optional[str]): Parent page ID if exists
            last_edited (datetime): Last edit time of the page
            description (str): Brief description of the page (e.g. title)
            task_details (str): The actual Notey task text

        Returns:
            NotionAgentJob: Created job instance
        """
        logger.debug(
            f"Creating agent job for page {page_id} "
            f"(parent: {parent_page_id or 'None'}, "
            f"last_edited: {last_edited.isoformat()})"
        )
        job = NotionAgentJob.objects.create(
            page_id=page_id,
            parent_page_id=parent_page_id if parent_page_id else None,  # Explicitly set None if no parent
            page_url=f"https://notion.so/{page_id.replace('-', '')}",
            description=description,
            task_details=task_details,
            notion_updated_at=last_edited,
        )
        logger.debug(f"Created agent job with ID: {job.id}")
        return job

    def process_job(self, job: NotionAgentJob) -> None:
        """
        Process a Notion agent job.

        Args:
            job (NotionAgentJob): The job to process
        """
        logger.debug(f"Processing job {job.id} for page {job.page_id}")

        try:
            # Get the latest page content
            self.get_page(job.page_id) if job.page_id else None
            page_content = self.get_page_content(job.page_id)

            # Check if the page still has the Notey content
            notey_text = self.has_notey_content(page_content)

            if not notey_text:
                logger.info(f"Notey content no longer found in page {job.page_id}")
                job.status = NotionAgentJob.Status.COMPLETED
                job.result = "Notey content removed from page"
                job.completed_at = timezone.now()
                job.save()
                return

            # If the Notey content changed, create a new job
            if notey_text != job.task_details:
                logger.info(f"Notey content changed in page {job.page_id}")
                # Mark current job as completed
                job.status = NotionAgentJob.Status.COMPLETED
                job.result = "Notey content changed, created new job"
                job.completed_at = timezone.now()
                job.save()

                # Create new job with updated content
                self.create_agent_job(
                    page_id=job.page_id,
                    parent_page_id=job.parent_page_id,
                    last_edited=timezone.now(),
                    description=job.description,
                    task_details=notey_text,
                )
                return

            # TODO: Implement actual job processing logic here
            # For now, just mark as completed
            job.status = NotionAgentJob.Status.COMPLETED
            job.result = "Job processed successfully"
            job.completed_at = timezone.now()
            job.save()

        except Exception as e:
            logger.error(f"Error processing job {job.id}: {str(e)}")
            job.status = NotionAgentJob.Status.FAILED
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()
            raise
