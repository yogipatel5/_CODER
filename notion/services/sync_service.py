import logging
from datetime import datetime
from typing import Dict, List

from celery import group
from django.conf import settings

from notion.api.client import NotionClient
from notion.models.database import Database
from notion.models.page import Page
from notion.tasks.database_sync import sync_database

logger = logging.getLogger(__name__)


class NotionSyncService:
    """Service for syncing Notion content."""

    # TODO: Add transaction support for database operations
    # TODO: Implement proper error recovery mechanisms
    # TODO: Add metrics collection for sync operations
    # TODO: Consider implementing incremental sync
    def __init__(self):
        self.client = NotionClient()
        self.synced_database_page_ids = set()  # Track pages that are part of databases

        # Cache existing pages and databases
        self._cache_existing_items()

    def _cache_existing_items(self):
        """Cache existing pages and databases for faster comparison."""
        # Format: {id: last_edited_time}
        self.existing_pages = {page.id: page.last_edited_time for page in Page.objects.all()}
        self.existing_databases = {db.id: db.last_edited_time for db in Database.objects.all()}

    def _parse_notion_timestamp(self, timestamp: str) -> datetime:
        """Parse Notion timestamp to datetime."""
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def _needs_update(self, item_id: str, last_edited_time: datetime, is_database: bool) -> bool:
        """Check if an item needs to be updated based on its last_edited_time."""
        existing_items = self.existing_databases if is_database else self.existing_pages
        if item_id not in existing_items:
            return True

        existing_time = existing_items[item_id]
        return last_edited_time > existing_time

    def _is_database_page(self, page_data: Dict) -> bool:
        """Check if a page is a row in a database."""
        parent = page_data.get("parent", {})
        return parent.get("type") == "database_id"

    def sync_pages(self):
        """Sync all pages from Notion."""
        pages = self.client.search_pages("")
        logger.info(f"Found {len(pages)} items in search results")

        synced_pages = 0
        skipped_databases = 0
        skipped_database_pages = 0
        skipped_unchanged = 0

        for page_data in pages:
            # Skip if this is a database
            if page_data.get("object") == "database":
                skipped_databases += 1
                continue

            # Skip if this is a page in a database - these will be handled by sync_project_databases
            if self._is_database_page(page_data):
                skipped_database_pages += 1
                continue

            # Check if page needs update
            last_edited_time = self._parse_notion_timestamp(page_data["last_edited_time"])
            if not self._needs_update(page_data["id"], last_edited_time, is_database=False):
                skipped_unchanged += 1
                continue

            # Extract title from properties
            title = ""
            if "properties" in page_data and "title" in page_data["properties"]:
                title_blocks = page_data["properties"]["title"].get("title", [])
                title = " ".join(block.get("plain_text", "") for block in title_blocks)

            # Parse parent information
            parent = page_data.get("parent", {})
            parent_type = parent.get("type", "workspace")
            parent_id = parent.get(parent_type) if parent_type != "workspace" else None

            # Parse timestamps - they come in as UTC ISO format
            created_time = self._parse_notion_timestamp(page_data["created_time"])

            # Fetch page blocks (content) only if needed
            blocks = self.client.get_block_children(page_data["id"])

            # Create or update the page
            page, created = Page.objects.update_or_create(
                id=page_data["id"],
                defaults={
                    "created_time": created_time,
                    "last_edited_time": last_edited_time,
                    "cover": page_data.get("cover"),
                    "icon": page_data.get("icon"),
                    "parent_type": parent_type,
                    "parent_id": parent_id,
                    "archived": page_data.get("archived", False),
                    "in_trash": page_data.get("in_trash", False),
                    "title": title,
                    "url": page_data["url"],
                    "public_url": page_data.get("public_url"),
                    "raw_properties": page_data.get("properties", {}),
                    "blocks": blocks,
                },
            )
            synced_pages += 1
            logger.info(f"{'Created' if created else 'Updated'} page: {title} ({page.id})")

        logger.info(
            "Synced {} pages, skipped {} databases, {} database pages, "
            "and {} unchanged pages".format(synced_pages, skipped_databases, skipped_database_pages, skipped_unchanged)
        )

    def sync_project_databases(self):
        """Sync databases from the project page."""
        project_page_id = getattr(settings, "NOTION_PROJECT_PAGE_ID", None)
        if not project_page_id:
            logger.warning("NOTION_PROJECT_PAGE_ID not set in settings")
            return

        # Clean page ID (remove any dashes)
        project_page_id = project_page_id.replace("-", "")

        # Get all blocks from the project page
        blocks = self.client.get_block_children(project_page_id)
        logger.info(f"Found {len(blocks)} blocks in project page")

        # Filter for child_database blocks
        database_blocks = [b for b in blocks if b.get("type") == "child_database"]
        logger.info(f"Found {len(database_blocks)} databases in project page")

        # Create a group of tasks to sync databases in parallel
        tasks = []
        for block in database_blocks:
            database_id = block["id"]
            title = block["child_database"]["title"]

            # Get database metadata to check last_edited_time
            database = self.client.get_database(database_id)
            last_edited_time = self._parse_notion_timestamp(database["last_edited_time"])

            # Skip if database hasn't changed
            if not self._needs_update(database_id, last_edited_time, is_database=True):
                logger.info(f"Skipping unchanged database: {title} ({database_id})")
                continue

            tasks.append(sync_database.s(database_id=database_id, title=title))

        if tasks:
            # Execute tasks in parallel and continue without waiting
            group(tasks).apply_async()
            logger.info(f"Scheduled {len(tasks)} database sync tasks")
        else:
            logger.info("No database updates needed")

    def update_database(self, database_id: str, title: str, database: Dict, database_items: List[Dict]):
        """Update a database and its items."""
        created_time = self._parse_notion_timestamp(database["created_time"])
        last_edited_time = self._parse_notion_timestamp(database["last_edited_time"])

        # Create or update database
        db, created = Database.objects.update_or_create(
            id=database_id,
            defaults={
                "title": title,
                "parent_page_id": settings.NOTION_PROJECT_PAGE_ID.replace("-", ""),
                "created_time": created_time,
                "last_edited_time": last_edited_time,
                "properties_schema": database.get("properties", {}),
                "rows": database_items,
            },
        )
        logger.info(
            f"{'Created' if created else 'Updated'} database: {title} ({db.id}) with {len(database_items)} rows"
        )

    def sync_all(self):
        """Sync all Notion content (pages and databases)."""
        logger.info("Starting Notion sync")
        self.sync_pages()
        self.sync_project_databases()
        logger.info("Sync completed successfully")
        return "Sync completed successfully"
