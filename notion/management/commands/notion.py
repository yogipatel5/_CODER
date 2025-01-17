"""
Main router for Notion management commands.
"""

import importlib
from pathlib import Path
from typing import Dict, Type

from django.core.management.base import BaseCommand, CommandError

from .base_command import NotionBaseCommand


class Command(BaseCommand):
    """Notion management commands"""

    help = "Notion management commands"

    def __init__(self):
        super().__init__()
        self.commands: Dict[str, Type[NotionBaseCommand]] = {}
        self._load_commands()

    def _load_commands(self):
        """Dynamically load all available commands."""
        current_dir = Path(__file__).parent

        # Load commands from main directory
        for file in current_dir.glob("*.py"):
            if file.stem in ["__init__", "notion", "base_command"]:
                continue
            self._try_load_command(file)

        # Load commands from run directory
        run_dir = current_dir / "run"
        if run_dir.exists():
            for file in run_dir.glob("*.py"):
                if file.stem != "__init__":
                    self._try_load_command(file, "run")

    def _try_load_command(self, file: Path, subdir: str = ""):
        """Try to load a command from a file."""
        try:
            module_path = "notion.management.commands"
            if subdir:
                module_path += f".{subdir}"
            module_path += f".{file.stem}"

            module = importlib.import_module(module_path)
            if hasattr(module, "Command"):
                command_class = getattr(module, "Command")
                # Instantiate the command to trigger tool registration
                command_class()
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
        command.stdout = self.stdout  # Pass stdout to subcommand
        command.stderr = self.stderr  # Pass stderr to subcommand
        return command.handle(*args, **options)
