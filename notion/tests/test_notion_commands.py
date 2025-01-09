"""
Tests for Notion management commands.
Both unit tests with mocked responses and real-world integration tests.
"""

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
        self.mock_database = {"id": "test_db_id", "title": [{"text": {"content": "Test Database"}}]}

        self.mock_page = {
            "id": "test_page_id",
            "properties": {
                "title": {"title": [{"text": {"content": "Test Page"}}]},
                "Status": {"select": {"name": "In Progress"}},
            },
        }

    @patch("notion.management.commands.base.NotionAPI.list_databases")
    def test_list_databases(self, mock_list):
        mock_list.return_value = [self.mock_database]
        call_command("notion", "list_databases", stdout=self.stdout)
        self.assertIn("Test Database", self.stdout.getvalue())

    @patch("notion.management.commands.base.NotionAPI.get_page")
    def test_get_page(self, mock_get):
        mock_get.return_value = self.mock_page
        call_command("notion", "get_page", "test_page_id", stdout=self.stdout)
        self.assertIn("Test Page", self.stdout.getvalue())


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
        output = self.stdout.getvalue()
        # Verify output format and save a database_id for later tests
        self.assertIn("Found", output)
        # TODO: Save a database_id for subsequent tests

    def test_02_create_test_page(self):
        """Create a test page in the selected database."""
        database_id = "YOUR_TEST_DATABASE_ID"  # We'll get this from manual testing first
        call_command(
            "notion",
            "create_page",
            database_id,
            "--title",
            "Integration Test Page",
            "--properties",
            "Status=Testing",
            stdout=self.stdout,
        )
        output = self.stdout.getvalue()
        # Extract and save the created page ID for later tests
        # self.created_pages.append(page_id)

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
