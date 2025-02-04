import importlib
import inspect
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "DJHelper management commands"

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        self.add_subcommands(parser)
        return parser

    def _get_command_modules(self):
        """Dynamically discover all command modules in this directory."""
        current_dir = Path(__file__).parent
        commands = {}

        # Skip these files
        skip_files = {"djhelper.py", "__init__.py"}

        for file_path in current_dir.glob("*.py"):
            if file_path.name not in skip_files:
                module_name = file_path.stem
                try:
                    # Import the module
                    module = importlib.import_module(f".{module_name}", package=__package__)

                    # Find the Command class
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and name == "Command" and obj.__module__ == module.__name__:
                            # Add both snake_case and kebab-case versions
                            snake_case = module_name
                            kebab_case = module_name.replace("_", "-")

                            # Add both versions to commands dict
                            commands[snake_case] = obj
                            if snake_case != kebab_case:
                                commands[kebab_case] = obj
                            break
                except ImportError as e:
                    self.stderr.write(f"Failed to import {module_name}: {e}")

        return commands

    def add_subcommands(self, parser):
        subparsers = parser.add_subparsers(title="subcommands", dest="subcommand")

        # Dynamically add all discovered commands
        for cmd_name, cmd_class in self._get_command_modules().items():
            subparser = subparsers.add_parser(cmd_name, help=cmd_class.help)
            cmd = cmd_class()
            cmd.add_arguments(subparser)

    def handle(self, *args, **options):
        if not options["subcommand"]:
            self.print_help("manage.py", "djhelper")
            return

        # Get the command class
        commands = self._get_command_modules()
        cmd_class = commands[options["subcommand"]]

        # Create and run the command
        cmd = cmd_class()

        # Extract all options except 'subcommand' and pass them to the command
        cmd_options = {k: v for k, v in options.items() if k != "subcommand"}
        cmd.execute(**cmd_options)
