# """
# Tests for Notion management commands.
# """

# from django.test import TestCase

# from notion.management.commands.base_command import REGISTERED_NOTION_TOOLS
# from notion.management.commands.run.create_page import Command as CreatePageCommand
# from notion.management.commands.run.create_page import CreatePageNotionTool
# from notion.management.commands.run.list_pages import Command as ListPagesCommand
# from notion.management.commands.run.list_pages import ListPagesNotionTool


# class TestNotionCommands(TestCase):
#     """Test cases for Notion management commands."""

#     @classmethod
#     def setUpClass(cls):
#         """Set up test environment."""
#         super().setUpClass()
#         # Instantiate commands to trigger registration
#         ListPagesCommand()
#         CreatePageCommand()

#     def test_automatic_tool_registration(self):
#         """Test that tools are automatically registered when commands are imported."""
#         # Get list of registered tool names
#         registered_tool_names = [tool.name for tool in REGISTERED_NOTION_TOOLS]

#         # Verify that both tools are registered
#         self.assertIn("list_notion_pages", registered_tool_names)
#         self.assertIn("create_notion_page", registered_tool_names)

#         # Verify tool types
#         list_tool = next(tool for tool in REGISTERED_NOTION_TOOLS if tool.name == "list_notion_pages")
#         self.assertIsInstance(list_tool, ListPagesNotionTool)

#         create_tool = next(tool for tool in REGISTERED_NOTION_TOOLS if tool.name == "create_notion_page")
#         self.assertIsInstance(create_tool, CreatePageNotionTool)
