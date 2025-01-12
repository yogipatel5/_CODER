"""
Tools for Notion management commands.
"""

import logging

from notion.management.commands.run.create_page import Command as CreatePageCommand
from notion.management.commands.run.list_pages import Command as ListPagesCommand
from notion.management.commands.base_command import NotionBaseCommand

logger = logging.getLogger(**name**)

# Instantiate commands to trigger tool registration

CreatePageCommand()
ListPagesCommand()

# Access the registered tools from the base command

NOTION_TOOLS = NotionBaseCommand.registered_tools
