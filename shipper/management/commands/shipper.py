import importlib
import inspect
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "shipper management commands"

    def create_parser(self, prog_name, subcommand, **kwargs):
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        self.add_subcommands(parser)
        return parser

    def _get_command_modules(self):
        """Dynamically discover all command modules in this directory."""
        current_dir = Path(__file__).parent
        commands = {}

        # Skip these files
        skip_files = {"shipper.py", "__init__.py", "README.md"}

        for file_path in current_dir.glob("*.py"):
            if file_path.name not in skip_files:
                module_name = file_path.stem
                try:
                    # Import the module
                    module = importlib.import_module(f".{module_name}", package=__package__)

                    # Find the Command class
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) and name == "Command" and obj.__module__ == module.__name__:
                            # Convert module_name from snake_case to kebab-case for CLI
                            cli_name = module_name.replace("_", "-")
                            commands[cli_name] = obj
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
        subcommand = options["subcommand"]
        if not subcommand:
            self.print_help("manage.py", "shipper")
            return

        # Convert kebab-case back to snake_case for module lookup
        module_name = subcommand.replace("-", "_")
        try:
            module = importlib.import_module(f".{module_name}", package=__package__)
            cmd_class = getattr(module, "Command")
            cmd = cmd_class()
            cmd.handle(**options)
        except (ImportError, AttributeError) as e:
            self.stderr.write(f"Failed to run command {subcommand}: {e}")
