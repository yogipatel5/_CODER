# Django Management Commands

This directory contains management commands for the pfsense app. Commands are organized using a namespace system.

## Command Structure

```
management/
├── __init__.py
└── commands/
    ├── __init__.py
    ├── pfsense.py     # Parent command (handles subcommands)
    ├── setup.py              # Initial app setup and configuration
    └── ...                   # Additional subcommands
```

## Usage

All commands in this app are namespaced under `pfsense`. To run a command:

```bash
python manage.py pfsense <subcommand> [options]
```

### Available Commands

1. **setup**: Initialize app configuration and data
   ```bash
   python manage.py pfsense setup [--force]
   ```
   - Sets up periodic tasks
   - Initializes required data
   - Use `--force` to re-run setup even if already configured

## Adding New Commands

1. Create a new Python file in the `commands` directory (e.g., `my_command.py`)
2. The filename will become the subcommand name (converted to kebab-case)
3. Implement the command class following Django's conventions:

```python
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Description of what your command does"

    def add_arguments(self, parser):
        # Add command arguments here
        parser.add_argument("--example", type=str, help="Example argument")

    def handle(self, *args, **options):
        # Implement command logic here
        self.stdout.write(self.style.SUCCESS("Command executed successfully"))
```

The command will automatically be discovered and available as:

```bash
python manage.py pfsense my-command --example "value"
```
