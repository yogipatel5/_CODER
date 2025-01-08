"""
Main router for Notion management commands.
"""

import importlib
from pathlib import Path
from typing import Dict, Type

from django.core.management.base import BaseCommand, CommandError

from .base import NotionBaseCommand


class Command(BaseCommand):
    help = "Notion management commands"

    def __init__(self):
        super().__init__()
        self.commands: Dict[str, Type[NotionBaseCommand]] = {}
        self._load_commands()

    def _load_commands(self):
        """Dynamically load all available commands."""
        current_dir = Path(__file__).parent
        for file in current_dir.glob("*.py"):
            if file.stem in ["__init__", "notion", "base"]:
                continue

            try:
                module = importlib.import_module(f"notion.management.commands.{file.stem}")
                if hasattr(module, "Command"):
                    command_class = getattr(module, "Command")
                    if issubclass(command_class, NotionBaseCommand):
                        self.commands[file.stem] = command_class
            except ImportError as e:
                self.stderr.write(f"Failed to load command {file.stem}: {e}")

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        subparsers = parser.add_subparsers(dest="subcommand", title="subcommands")

        # Add all available commands
        for name, command_class in self.commands.items():
            subparser = subparsers.add_parser(name, help=command_class.help)
            command_instance = command_class()
            command_instance.add_arguments(subparser)

        return parser

    def handle(self, *args, **options):
        if not options["subcommand"]:
            self.print_help("manage.py", "notion")
            return

        command_name = options["subcommand"]
        if command_name not in self.commands:
            raise CommandError(f"Unknown subcommand: {command_name}")

        # Create and run the appropriate command
        command = self.commands[command_name]()
        return command.handle(*args, **options)
