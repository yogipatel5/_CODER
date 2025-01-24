"""Service for handling Notey-related business logic."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from django.utils import timezone

from notion.api.client import NotionClient
from notion.models.notionagentjobs import NotionAgentJob

logger = logging.getLogger(__name__)


class NoteyService:
    """Service class for handling Notey-related business logic."""

    # TODO: Move block parsing logic to a dedicated BlockParser service
    # TODO: Add support for different Notey block types
    # TODO: Implement content validation rules
    # TODO: Add support for template-based responses
    def __init__(self):
        """Initialize Notion client."""
        logger.debug("Initializing NoteyService")
        self.client = NotionClient()

    def scan_pages_for_notey_content(self) -> List[Dict]:
        """
        Scan all pages for Notey content and return pages that have it.

        Returns:
            List[Dict]: List of pages containing Notey content
        """
        logger.debug("Starting scan for Notey content across all pages")
        pages = self.client.search_pages("")
        logger.debug(f"Retrieved {len(pages)} pages from Notion")
        notey_pages = []

        for page in pages:
            page_id = page.get("id")
            logger.debug(f"Processing page {page_id}")
            blocks = self.client.get_block_children(page_id)
            logger.debug(f"Retrieved {len(blocks)} blocks from page {page_id}")
            notey_text = self._extract_notey_content(blocks)

            if notey_text:
                logger.debug(f"Found Notey content in page {page_id}: {notey_text[:100]}...")
                notey_pages.append({"page": page, "notey_text": notey_text})

        logger.info(f"Found {len(notey_pages)} pages with Notey content")
        return notey_pages

    def _extract_notey_content(self, blocks: List[Dict]) -> Optional[str]:
        """
        Extract Notey content from blocks if present.

        Args:
            blocks (List[Dict]): List of blocks from the page

        Returns:
            Optional[str]: The Notey task text if found, None otherwise
        """
        logger.debug(f"Analyzing {len(blocks)} blocks for Notey content")

        for block in blocks:
            block_id = block.get("id")
            block_type = block.get("type")
            logger.debug(f"Processing block {block_id} of type {block_type}")
            text_content = self._get_block_text_content(block)

            if not text_content:
                logger.debug(f"No text content found in block {block_id}")
                continue

            if "Notey" in text_content:
                logger.debug(f"Found Notey content in block {block_id}: {text_content[:100]}...")
                return text_content.strip()

        logger.debug("No Notey content found in any blocks")
        return None

    def _get_block_text_content(self, block: Dict) -> str:
        """
        Extract text content from a block based on its type.

        Args:
            block (Dict): Block data

        Returns:
            str: Combined text content from the block
        """
        block_type = block.get("type")
        block_id = block.get("id")
        logger.debug(f"Extracting text content from block {block_id} of type {block_type}")

        text_segments = []
        if block_type in ["paragraph", "callout"]:
            text_segments = block.get(block_type, {}).get("rich_text", [])
            logger.debug(f"Found {len(text_segments)} text segments in {block_type} block {block_id}")

        text_content = " ".join(segment.get("plain_text", "") for segment in text_segments if segment.get("plain_text"))
        if text_content:
            logger.debug(f"Extracted text content from block {block_id}: {text_content[:100]}...")
        return text_content

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
            parent_page_id=parent_page_id,
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
        logger.debug(f"Starting to process job {job.id} for page {job.page_id}")
        logger.debug(f"Current job details - Status: {job.status}, Task: {job.task_details[:100]}...")

        try:
            # Get the latest page content
            blocks = self.client.get_block_children(job.page_id)
            logger.debug(f"Retrieved {len(blocks)} blocks from page {job.page_id}")
            notey_text = self._extract_notey_content(blocks)

            if not notey_text:
                logger.debug(f"Notey content no longer found in page {job.page_id}")
                self._complete_job(
                    job, status=NotionAgentJob.Status.COMPLETED, result="Notey content removed from page"
                )
                return

            # If the Notey content changed, create a new job
            if notey_text != job.task_details:
                logger.debug(
                    f"Notey content changed in page {job.page_id}\n"
                    f"Old content: {job.task_details[:100]}...\n"
                    f"New content: {notey_text[:100]}..."
                )
                self._handle_changed_notey_content(job, notey_text)
                return

            # TODO: Implement actual job processing logic here
            logger.debug(f"Processing job {job.id} with task: {job.task_details[:100]}...")
            self._complete_job(job, status=NotionAgentJob.Status.COMPLETED, result="Job processed successfully")

        except Exception as e:
            logger.error(f"Error processing job {job.id}: {str(e)}", exc_info=True)
            self._complete_job(job, status=NotionAgentJob.Status.FAILED, error_message=str(e))
            raise

    def _complete_job(
        self, job: NotionAgentJob, status: str, result: Optional[str] = None, error_message: Optional[str] = None
    ) -> None:
        """
        Complete a job with the given status and details.

        Args:
            job (NotionAgentJob): The job to complete
            status (str): Job status
            result (Optional[str]): Job result message
            error_message (Optional[str]): Error message if job failed
        """
        logger.debug(
            f"Completing job {job.id} - "
            f"Status: {status}, "
            f"Result: {result[:100] if result else 'None'}..., "
            f"Error: {error_message[:100] if error_message else 'None'}..."
        )

        job.status = status
        job.completed_at = timezone.now()

        if result:
            job.result = result
        if error_message:
            job.error_message = error_message

        job.save()
        logger.debug(f"Job {job.id} completed and saved")

    def _handle_changed_notey_content(self, job: NotionAgentJob, new_notey_text: str) -> None:
        """
        Handle a job where the Notey content has changed.

        Args:
            job (NotionAgentJob): The current job
            new_notey_text (str): The new Notey content
        """
        logger.debug(
            f"Handling changed Notey content for job {job.id}\n"
            f"Old content: {job.task_details[:100]}...\n"
            f"New content: {new_notey_text[:100]}..."
        )

        # Mark current job as completed
        self._complete_job(job, status=NotionAgentJob.Status.COMPLETED, result="Notey content changed, created new job")

        # Create new job with updated content
        logger.debug(f"Creating new job for page {job.page_id} with updated content")
        self.create_agent_job(
            page_id=job.page_id,
            parent_page_id=job.parent_page_id,
            last_edited=timezone.now(),
            description=job.description,
            task_details=new_notey_text,
        )
