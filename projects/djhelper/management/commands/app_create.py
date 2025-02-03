import shutil
from pathlib import Path

from django.core.management.base import BaseCommand
from django.template import Context, Template
from django.utils import timezone


class Command(BaseCommand):
    help = "Create a new Django app with the standard structure"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str, help="Name of the app to create")

    def _render_template(self, template_path: str, context: dict) -> str:
        """Render a template file with the given context."""
        with open(template_path, "r") as f:
            template = Template(f.read())
        return template.render(Context(context))

    def _copy_template_files(self, source_dir: Path, target_dir: Path, context: dict):
        """Copy template files from source to target directory."""
        if not source_dir.exists():
            return

        # Files to ignore
        IGNORE_FILES = {".DS_Store", "__pycache__", "*.pyc", ".git"}

        target_dir.mkdir(parents=True, exist_ok=True)

        for item in source_dir.rglob("*"):
            # Skip ignored files
            if any(ignore in str(item) for ignore in IGNORE_FILES):
                continue

            if item.is_file():
                # Calculate relative path from source root
                rel_path = item.relative_to(source_dir)

                # Replace placeholders in the path itself
                rel_path_str = str(rel_path)
                if "{{ app_name }}" in rel_path_str:
                    rel_path_str = rel_path_str.replace("{{ app_name }}", context["app_name"])
                target_path = target_dir / rel_path_str

                # Create parent directories if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # Remove .template extension if present
                if target_path.suffix == ".template":
                    target_path = target_path.with_suffix("")

                try:
                    # Try to render as a template
                    content = self._render_template(str(item), context)
                    target_path.write_text(content)
                    self.stdout.write(self.style.SUCCESS(f"Created: {target_path}"))
                except UnicodeDecodeError:
                    # If it's a binary file, just copy it as-is
                    shutil.copy2(item, target_path)
                    self.stdout.write(self.style.SUCCESS(f"Created binary file: {target_path}"))

    def _update_settings(self, app_name: str):
        """Add the new app to INSTALLED_APPS in settings.py."""
        # Find the root directory (where manage.py is)
        current_dir = Path.cwd()
        settings_path = current_dir / "core" / "settings.py"

        if not settings_path.exists():
            self.stdout.write(self.style.WARNING(f"Could not find settings.py at {settings_path}"))
            return

        content = settings_path.read_text()
        if f"'{app_name}'" not in content and f'"{app_name}"' not in content:
            # Find the INSTALLED_APPS list
            if "INSTALLED_APPS = [" in content:
                # Add the new app to INSTALLED_APPS
                new_content = content.replace(
                    "INSTALLED_APPS = [",
                    f"INSTALLED_APPS = [\n#    '{app_name}',",
                )
                settings_path.write_text(new_content)
                self.stdout.write(self.style.SUCCESS(f"Added '{app_name}' to INSTALLED_APPS"))

    def handle(self, *args, **options):
        app_name = options["app_name"]
        app_dir = Path.cwd() / app_name

        # Create app directory
        app_dir.mkdir(exist_ok=True)
        self.stdout.write(self.style.SUCCESS(f"Creating app directory: {app_dir}"))

        # Get template directory
        template_dir = Path(__file__).parent.parent.parent / "app_folder_template"
        if not template_dir.exists():
            self.stdout.write(self.style.ERROR(f"Template directory not found: {template_dir}"))
            return

        # Set up template context
        template_context = {
            "app_name": app_name,
            "app_name_capitalized": app_name.capitalize(),
            "created_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Copy all template files and directories
        self._copy_template_files(template_dir, app_dir, template_context)

        # Update settings.py
        self._update_settings(app_name)

        self.stdout.write(self.style.SUCCESS(f"Successfully created app structure for '{app_name}'"))
