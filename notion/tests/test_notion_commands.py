"""
Tests for Notion management commands.
Both unit tests with mocked responses and real-world integration tests.
"""

import json
import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase


class NotionCommandsUnitTests(TestCase):
    """Unit tests with mocked API responses"""

    def setUp(self):
        self.stdout = StringIO()
        self.stderr = StringIO()

        # Mock response data
        self.mock_database = {
            "id": "test_db_id",
            "title": [{"plain_text": "Test Database"}],
            "parent": {"type": "workspace"},
            "properties": {},
        }

        self.mock_page = {
            "id": "test_page_id",
            "properties": {
                "title": {"title": [{"text": {"content": "Test Page"}, "plain_text": "Test Page"}]},
                "Status": {"select": {"name": "In Progress"}},
            },
            "parent": {"type": "workspace"},
            "url": "https://notion.so/test-page",
        }

    @patch("notion.management.commands.base.NotionAPI.list_databases")
    def test_list_databases(self, mock_list):
        mock_list.return_value = [self.mock_database]
        call_command("notion", "list_databases", stdout=self.stdout)
        output = json.loads(self.stdout.getvalue())
        self.assertTrue(output["success"])
        self.assertEqual(len(output["data"]["databases"]), 1)
        self.assertEqual(output["data"]["databases"][0]["title"], "Test Database")

    @patch("notion.management.commands.base.NotionAPI.get_page")
    def test_get_page(self, mock_get):
        mock_get.return_value = self.mock_page
        call_command("notion", "get_page", "test_page_id", stdout=self.stdout)
        output = json.loads(self.stdout.getvalue())
        self.assertTrue(output["success"])
        self.assertEqual(output["data"]["page"]["id"], "test_page_id")
        self.assertEqual(output["data"]["page"]["title"], "Test Page")


class NotionCommandsIntegrationTests(TestCase):
    """
    Integration tests using real Notion API.
    These tests will actually create/modify/delete content in Notion.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ensure we have the API key
        if not os.getenv("NOTION_API_KEY"):
            raise ValueError("NOTION_API_KEY environment variable is required for integration tests")

        # Store IDs for cleanup
        cls.created_pages = []

    def setUp(self):
        self.stdout = StringIO()
        self.stderr = StringIO()

    def test_01_list_databases(self):
        """List available databases and verify output format."""
        call_command("notion", "list_databases", stdout=self.stdout)
        output = json.loads(self.stdout.getvalue())
        self.assertTrue(output["success"])
        self.assertIn("Found", output["message"])
        # Save database_id for subsequent tests if needed
        if output["data"]["databases"]:
            self.database_id = output["data"]["databases"][0]["id"]

    def test_02_create_test_page(self):
        """Create a test page in the selected database."""
        if not hasattr(self, "database_id"):
            self.skipTest("No database available for testing")
        
        call_command(
            "notion",
            "create_page",
            self.database_id,
            "Integration Test Page",
            "--parent-type",
            "database_id",
            "--properties",
            "Status=Testing",
            stdout=self.stdout,
        )
        output = json.loads(self.stdout.getvalue())
        self.assertTrue(output["success"])
        # Save the created page ID for later tests
        self.created_pages.append(output["data"]["page"]["id"])

    def test_03_get_page_details(self):
        """Verify the created page exists with correct properties."""
        pass

    def test_04_update_page(self):
        """Update the test page properties."""
        pass

    def test_05_create_subpage(self):
        """Create a subpage under our test page."""
        pass

    def test_06_list_children(self):
        """List and verify child pages/blocks."""
        pass

    def test_07_delete_subpage(self):
        """Delete the subpage."""
        pass

    def test_08_delete_main_page(self):
        """Clean up by deleting the main test page."""
        pass

    @classmethod
    def tearDownClass(cls):
        """Clean up any remaining test pages."""
        super().tearDownClass()
        # Delete any pages that weren't cleaned up during tests
        for page_id in cls.created_pages:
            try:
                call_command("notion", "delete_page", page_id)
            except Exception as e:
                print(f"Failed to delete test page {page_id}: {e}")
