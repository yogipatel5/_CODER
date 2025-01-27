import os
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates a new Django app with a predefined structure following best practices"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str, help="Name of the Django app to create")
        parser.add_argument("--path", type=str, default=".", help="Path where the app should be created")

    def handle(self, *args, **options):
        app_name = options["app_name"]
        base_path = Path(options["path"]) / app_name

        # Define the directory structure
        directories = [
            "",  # Root directory
            "admin",
            "api",
            "management/commands",
            "managers",
            "models",
            "services",
            "tasks",
            "docs",
        ]

        # Create directories
        for directory in directories:
            dir_path = base_path / directory
            os.makedirs(dir_path, exist_ok=True)
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()

        # Create apps.py
        apps_content = f'''from django.apps import AppConfig
from pathlib import Path


class {app_name.capitalize()}Config(AppConfig):
    """Django app configuration for {app_name}."""

    name = "{app_name}"
    default_auto_field = "django.db.models.BigAutoField"

    def _import_modules_from_directory(self, directory_name: str):
        """
        Dynamically import all Python modules from a specified directory.

        Args:
            directory_name (str): Name of the directory to import modules from
        """
        app_path = Path(__file__).resolve().parent
        directory_path = app_path / directory_name

        if not directory_path.exists():
            return

        for file_path in directory_path.glob("*.py"):
            if file_path.name == "__init__.py":
                continue

            module_name = f"{{self.name}}.{{directory_name}}.{{file_path.stem}}"
            try:
                __import__(module_name)
            except ImportError as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to import {{module_name}}: {{str(e)}}")

    def ready(self):
        """
        Initialize app and register components.
        Auto-discovers and imports modules from specific directories.
        """
        # Auto-discover modules from these directories
        directories_to_import = ['admin', 'models', 'tasks']
        for directory in directories_to_import:
            self._import_modules_from_directory(directory)
'''

        with open(base_path / "apps.py", "w") as f:
            f.write(apps_content)

        # Create project structure documentation
        docs_content = """# Developer Instructions

This app is registered with Django.

apps.py is setting up auto discover for the models, tasks, and admin files.

## Project Structure Overview

### Admin Files (`admin/`)
- Follow the naming convention: `{model_name}admin.py`
- Each admin file should register its corresponding model

### Tasks (`tasks/`)
- Contains Celery task definitions
- Each task file should focus on a specific domain
- Use appropriate decorators (`@shared_task`)
- Include proper error handling and logging

### Models (`models/`)
- Each model should be in its own file
- Follow Django model best practices
- Complex querying logic should use model managers
- Do not put function or class definitions in models

### Model Managers (`managers/`)
- Contains manager classes for handling model operations
- Each model should have a corresponding manager file
- Keep business logic in services not in managers

### API (`api/`)
- Implement API clients and interfaces here
- Include proper error handling and rate limiting

### Services (`services/`)
- Business logic layer between API and models
- Keep services focused and single-responsibility

### Management Commands (`management/commands/`)
- Custom Django management commands
- Follow the pattern in existing commands
- Include help text and command documentation

## Development Guidelines

1. **Code Organization**
   - Keep related functionality together
   - Follow existing patterns for new files

2. **Documentation**
   - Include docstrings for all classes and methods
   - Keep documentation up-to-date

3. **Error Handling**
   - Implement proper exception handling
   - Use appropriate logging levels

4. **Testing**
   - Write tests for new functionality
   - Include both unit and integration tests
"""

        with open(base_path / "docs" / "project_structure.md", "w") as f:
            f.write(docs_content)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created app "{app_name}" with the following structure:\n'
                f"- admin/: For admin model registrations\n"
                f"- api/: For API clients and interfaces\n"
                f"- management/commands/: For custom management commands\n"
                f"- managers/: For model managers\n"
                f"- models/: For Django models\n"
                f"- services/: For business logic\n"
                f"- tasks/: For Celery tasks\n"
                f"- docs/: For documentation\n\n"
                f'Remember to add "{app_name}" to INSTALLED_APPS in your settings.py'
            )
        )
