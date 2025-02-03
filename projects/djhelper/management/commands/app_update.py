import shutil
from pathlib import Path

from django.core.management.base import BaseCommand
from django.template import Context, Template
from django.utils import timezone


class Command(BaseCommand):
    help = "Update an existing Django app with the latest template structure"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str, help="Name of the app to update")
        parser.add_argument(
            "--dryrun",
            action="store_true",
            help="Show what would be updated without making changes",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            help="Force update even if files exist",
        )
        parser.add_argument(
            "--backup",
            action="store_true",
            help="Create backup of existing files before updating",
        )

    def _render_template(self, template_path: str, context: dict) -> str:
        """Render a template file with the given context."""
        with open(template_path, "r") as f:
            template = Template(f.read())
        return template.render(Context(context))

    def _create_backup(self, target_dir: Path) -> Path:
        """Create a backup of the target directory."""
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = target_dir.parent / f"{target_dir.name}_backup_{timestamp}"
        shutil.copytree(target_dir, backup_dir)
        self.stdout.write(self.style.SUCCESS(f"Created backup at: {backup_dir}"))
        return backup_dir

    def _copy_template_files(self, source_dir: Path, target_dir: Path, context: dict, dry_run: bool, force: bool):
        """Copy template files from source to target directory."""
        if not source_dir.exists():
            return

        # Files to ignore
        IGNORE_FILES = {".DS_Store", "__pycache__", "*.pyc", ".git"}

        target_dir.mkdir(parents=True, exist_ok=True)

        # Track what would be updated
        would_update = []
        would_create = []
        would_skip = []

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

                # Remove .template extension if present
                if target_path.suffix == ".template":
                    target_path = target_path.with_suffix("")

                # Check if file exists
                if target_path.exists() and not force:
                    would_skip.append(target_path)
                    continue

                if target_path.exists():
                    would_update.append(target_path)
                else:
                    would_create.append(target_path)

                if not dry_run:
                    try:
                        # Create parent directories if needed
                        target_path.parent.mkdir(parents=True, exist_ok=True)

                        # Try to render as a template
                        content = self._render_template(str(item), context)
                        target_path.write_text(content)
                        self.stdout.write(
                            self.style.SUCCESS(f"{'Updated' if target_path.exists() else 'Created'}: {target_path}")
                        )
                    except UnicodeDecodeError:
                        # If it's a binary file, just copy it as-is
                        shutil.copy2(item, target_path)
                        self.stdout.write(self.style.SUCCESS(f"Copied binary file: {target_path}"))

        # Print summary for dry run
        if dry_run:
            if would_create:
                self.stdout.write("\nWould create:")
                for path in would_create:
                    self.stdout.write(f"  {path}")
            if would_update:
                self.stdout.write("\nWould update:")
                for path in would_update:
                    self.stdout.write(f"  {path}")
            if would_skip:
                self.stdout.write("\nWould skip (use --overwrite to update):")
                for path in would_skip:
                    self.stdout.write(f"  {path}")

    def handle(self, *args, **options):
        app_name = options["app_name"]
        dry_run = options["dryrun"]
        backup = options["backup"]

        # Get app directory - don't try to import, just use the path
        app_dir = Path.cwd() / app_name
        if not app_dir.exists():
            self.stdout.write(self.style.ERROR(f"App directory not found: {app_dir}"))
            return

        # Create backup if requested
        if backup and not dry_run:
            self._create_backup(app_dir)

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

        if dry_run:
            self.stdout.write(self.style.WARNING("\nDRY RUN - No changes will be made"))

        # Copy all template files and directories - force=True to create missing files
        self._copy_template_files(template_dir, app_dir, template_context, dry_run, True)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"\nDRY RUN complete. Run without --dryrun to update app '{app_name}'")
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully updated app structure for '{app_name}'"))
