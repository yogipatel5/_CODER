import shutil
from pathlib import Path

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Delete a Django app and remove it from INSTALLED_APPS"

    def add_arguments(self, parser):
        parser.add_argument("app_name", type=str, help="Name of the app to delete")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def _remove_from_settings(self, app_name: str, dry_run: bool = False) -> bool:
        """Remove the app from INSTALLED_APPS in settings.py."""
        settings_path = Path.cwd() / "core" / "settings.py"
        if not settings_path.exists():
            self.stdout.write(self.style.WARNING(f"Could not find settings.py at {settings_path}"))
            return False

        content = settings_path.read_text()
        lines = content.splitlines()
        app_found = False
        new_lines = []

        for line in lines:
            # Skip any line that has our app name
            if f'"{app_name}"' in line or f"'{app_name}'" in line:
                app_found = True
                self.stdout.write(f"Found app in settings.py: {line.strip()}")
                continue
            new_lines.append(line)

        if not app_found:
            self.stdout.write(self.style.WARNING(f"App '{app_name}' not found in INSTALLED_APPS"))
            return False

        if not dry_run:
            settings_path.write_text("\n".join(new_lines))
            self.stdout.write(self.style.SUCCESS(f"Removed '{app_name}' from INSTALLED_APPS"))

        return True

    def _delete_app_directory(self, app_name: str, dry_run: bool = False) -> bool:
        """Delete the app directory."""
        app_dir = Path.cwd() / app_name
        if not app_dir.exists():
            self.stdout.write(self.style.WARNING(f"App directory not found: {app_dir}"))
            return False

        if dry_run:
            self.stdout.write(f"Would delete directory: {app_dir}")
            for item in app_dir.rglob("*"):
                self.stdout.write(f"  Would delete: {item}")
            return True

        try:
            shutil.rmtree(app_dir)
            self.stdout.write(self.style.SUCCESS(f"Deleted app directory: {app_dir}"))
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error deleting directory: {str(e)}"))
            return False

    def handle(self, *args, **options):
        app_name = options["app_name"]
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes will be made"))

        # First try to remove from settings
        settings_removed = self._remove_from_settings(app_name, dry_run)

        # Then try to delete the directory
        directory_deleted = self._delete_app_directory(app_name, dry_run)

        if not (settings_removed or directory_deleted):
            self.stdout.write(
                self.style.ERROR(f"App '{app_name}' not found in INSTALLED_APPS or directory does not exist")
            )
            return

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"DRY RUN complete. Run without --dry-run to delete app '{app_name}'"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted app '{app_name}'"))
