# Notion Management Commands

This directory contains Django management commands for interacting with the Notion API. The structure is designed to be modular and easily extensible.

## Directory Structure

```
notion/management/commands/
├── __init__.py
├── base.py           # Base classes and API client
├── notion.py         # Command router and namespace (python manage [namespace] [command])
├── list_databases.py # python manage.py notion list_databases
├── create_page.py    # python manage.py notion create_page
└── search_pages.py   # python manage.py notion search_pages
```

## Core Components

### 1. Base Classes (`base.py`)

- `NotionAPI`: Client for interacting with Notion's API
  - Handles authentication
  - Provides base API methods
  - Manages HTTP requests and responses

- `NotionBaseCommand`: Base class for all command implementations
  - Inherits from Django's BaseCommand
  - Provides common utilities and API access
  - Standardizes command structure

### 2. Command Router (`notion.py`)

- Dynamically discovers and loads commands
- Maintains the command namespace
- Handles command registration and execution
- Routes commands to their appropriate handlers

## Adding New Functionality

### 1. Adding New API Methods

To add new API functionality:

1. Open `base.py`
2. Add your method to the `NotionAPI` class:

```python
class NotionAPI:
    def your_new_method(self, param1: str) -> Dict:
        """Documentation for your method."""
        endpoint = f"{self.base_url}/your-endpoint"
        data = {"key": param1}
        response = requests.post(endpoint, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
```

### 2. Creating New Commands

1. Create a new Python file (e.g., `your_command.py`):

```python
from .base import NotionBaseCommand

class Command(NotionBaseCommand):
    help = "Your command description"

    def add_arguments(self, parser):
        parser.add_argument("arg1", help="First argument")
        parser.add_argument("--optional", help="Optional argument")

    def handle(self, *args, **options):
        result = self.api.your_new_method(options["arg1"])
        self.stdout.write(self.style.SUCCESS("Operation successful"))
```

The command will be automatically discovered and available as:
```bash
python manage.py notion your_command arg1 --optional value
```

### 3. Adding Utility Functions

For shared functionality across commands:

1. Add utility methods to `NotionBaseCommand`:

```python
class NotionBaseCommand(BaseCommand):
    def your_utility(self, data: Dict) -> str:
        """Shared functionality for commands."""
        # Implementation
        return processed_result
```

2. Use in any command:

```python
class Command(NotionBaseCommand):
    def handle(self, *args, **options):
        data = self.api.some_method()
        result = self.your_utility(data)
```

## Best Practices

1. **Command Organization**
   - One command per file
   - Clear, descriptive file names
   - Comprehensive docstrings

2. **Error Handling**
   - Use try/except blocks for API calls
   - Provide meaningful error messages
   - Handle edge cases gracefully

3. **Code Style**
   - Follow PEP 8 guidelines
   - Use type hints
   - Add docstrings for all classes and methods

4. **Testing**
   - Add tests in `notion/tests/commands/`
   - Mock API calls in tests
   - Test edge cases and error conditions

## Example: Adding a "Delete Page" Command

1. Create `delete_page.py`:

```python
from .base import NotionBaseCommand

class Command(NotionBaseCommand):
    help = "Delete a Notion page"

    def add_arguments(self, parser):
        parser.add_argument("page_id", help="ID of the page to delete")
        parser.add_argument("--force", action="store_true", help="Skip confirmation")

    def handle(self, *args, **options):
        if not options["force"]:
            confirm = input(f"Delete page {options['page_id']}? [y/N] ")
            if confirm.lower() != 'y':
                self.stdout.write("Operation cancelled")
                return

        self.api.delete_page(options["page_id"])
        self.stdout.write(self.style.SUCCESS("Page deleted successfully"))
```

2. Add API method in `base.py`:

```python
class NotionAPI:
    def delete_page(self, page_id: str) -> None:
        endpoint = f"{self.base_url}/pages/{page_id}"
        response = requests.delete(endpoint, headers=self.headers)
        response.raise_for_status()
```

The command will be automatically available:
```bash
python manage.py notion delete_page your-page-id --force