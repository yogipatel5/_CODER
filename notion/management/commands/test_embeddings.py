import logging
import uuid

from django.core.management.base import BaseCommand
from django.utils import timezone

from notion.models.page import Page
from notion.services.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test embeddings functionality"

    def _create_test_page(self, content=None, model=None):
        """Create a test page with optional content and model."""
        page_id = str(uuid.uuid4())
        now = timezone.now()

        # Use real Notion blocks for testing
        blocks = [
            {
                "id": "18191679-55c8-805c-a9a9-e23fbab7a016",
                "type": "callout",
                "object": "block",
                "parent": {"type": "page_id", "page_id": page_id},
                "callout": {
                    "icon": {"type": "emoji", "emoji": "💡"},
                    "color": "gray_background",
                    "rich_text": [
                        {
                            "href": None,
                            "text": {
                                "link": None,
                                "content": "Notey: Can you please reoganize this and make it clearer and implement some mermaid as well - Remove from here once done and move to a new page under ",
                            },
                            "type": "text",
                            "plain_text": "Notey: Can you please reoganize this and make it clearer and implement some mermaid as well - Remove from here once done and move to a new page under ",
                            "annotations": {
                                "bold": False,
                                "code": False,
                                "color": "default",
                                "italic": False,
                                "underline": False,
                                "strikethrough": False,
                            },
                        },
                        {
                            "href": "https://www.notion.so/1819167955c881a9abe5ebe6a157cf00",
                            "type": "mention",
                            "mention": {"page": {"id": "18191679-55c8-81a9-abe5-ebe6a157cf00"}, "type": "page"},
                            "plain_text": "Shipbreeze",
                            "annotations": {
                                "bold": False,
                                "code": False,
                                "color": "default",
                                "italic": False,
                                "underline": False,
                                "strikethrough": False,
                            },
                        },
                        {
                            "href": None,
                            "text": {"link": None, "content": " thanks! "},
                            "type": "text",
                            "plain_text": " thanks! ",
                            "annotations": {
                                "bold": False,
                                "code": False,
                                "color": "default",
                                "italic": False,
                                "underline": False,
                                "strikethrough": False,
                            },
                        },
                    ],
                },
                "archived": False,
                "in_trash": False,
                "created_by": {"id": "d5f0653f-125a-46f7-bf9e-5228a8ce0a4c", "object": "user"},
                "created_time": "2025-01-20T17:04:00.000Z",
                "has_children": False,
                "last_edited_by": {"id": "d5f0653f-125a-46f7-bf9e-5228a8ce0a4c", "object": "user"},
                "last_edited_time": "2025-01-20T17:04:00.000Z",
            },
            {
                "id": "18191679-55c8-8015-ae50-ca319f70d3a0",
                "type": "paragraph",
                "object": "block",
                "parent": {"type": "page_id", "page_id": page_id},
                "archived": False,
                "in_trash": False,
                "paragraph": {
                    "color": "default",
                    "rich_text": [
                        {
                            "href": "https://www.notion.so/yp1016/Shipbreeze",
                            "text": {
                                "link": None,
                                "content": "This is a test paragraph with some content for embeddings testing.",
                            },
                            "type": "text",
                            "plain_text": "This is a test paragraph with some content for embeddings testing.",
                            "annotations": {
                                "bold": False,
                                "code": False,
                                "color": "default",
                                "italic": False,
                                "underline": False,
                                "strikethrough": False,
                            },
                        }
                    ],
                },
            },
        ]

        if content:
            # Add custom content block
            blocks.append(
                {
                    "id": str(uuid.uuid4()),
                    "type": "paragraph",
                    "object": "block",
                    "parent": {"type": "page_id", "page_id": page_id},
                    "archived": False,
                    "in_trash": False,
                    "paragraph": {
                        "color": "default",
                        "rich_text": [
                            {
                                "href": None,
                                "text": {"link": None, "content": content},
                                "type": "text",
                                "plain_text": content,
                                "annotations": {
                                    "bold": False,
                                    "code": False,
                                    "color": "default",
                                    "italic": False,
                                    "underline": False,
                                    "strikethrough": False,
                                },
                            }
                        ],
                    },
                }
            )

        page = Page.objects.create(
            id=page_id,
            created_time=now,
            last_edited_time=now,
            title=f"Test Page {page_id[:8]}",
            url=f"https://notion.so/{page_id}",
            content=content or "",
            blocks=blocks,
        )
        return page

    def handle(self, *args, **options):
        """Run the embeddings tests."""
        print("\nStarting embeddings tests...\n")

        # Initialize the embeddings service
        service = EmbeddingsService()

        # Test 1: Create a page with valid content and model
        print("1. Testing page creation with valid content and model...")
        page = self._create_test_page(content="This is a test page with some content.")
        print(f"Created page with ID: {page.id}")
        print(f"Task status: {page.search_metadata.get('task_status')}")
        print(f"Has embedding: {page.embedding is not None}")
        print()

        # Test 2: Create a page with no content
        print("2. Testing page creation with no content...")
        page_no_content = self._create_test_page()
        print(f"Created page with ID: {page_no_content.id}")
        print()

        # Test 3: Create a page with content exceeding max length
        print("3. Testing page with content exceeding max length...")
        long_content = "x" * 10000
        page_long = self._create_test_page(content=long_content)
        print(f"Created page with ID: {page_long.id}")
        print()

        # Test 4: Test direct service call with invalid model
        print("4. Testing direct service call with invalid model...")
        try:
            service.model = "invalid-model"
            service.update_page_embeddings(page)
            print("❌ Expected an error but got success")
        except Exception as e:
            print(f"✅ Got expected error: {str(e)}")
        print()

        # Test 5: Test direct service call with valid model
        print("5. Testing direct service call with valid model...")
        try:
            service.model = "text-embedding-nomic-embed-text-v1.5"
            service.update_page_embeddings(page)
            print("✅ Successfully updated embeddings with valid model")
            print(f"Has embedding: {page.embedding is not None}")
        except Exception as e:
            print(f"❌ Unexpected error with valid model: {str(e)}")
        print()

        # Test 6: Test page content update
        print("6. Testing page content update...")
        page.content = "Updated content"
        page.save()
        print(f"Updated page {page.id}")
        print()

        # Final status check
        print("Final status check for all pages:")
        for test_page in [page, page_no_content, page_long]:
            print(f"Page {test_page.id} status: {test_page.search_metadata.get('task_status')}")
            print(f"Has embedding: {test_page.embedding is not None}")
        print()

        print("Test complete!")
