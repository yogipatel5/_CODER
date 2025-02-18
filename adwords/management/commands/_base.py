from django.core.management.base import BaseCommand


class adwords_HelperCommand(BaseCommand):
    """Base command class for adwords management commands."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def log_success(self, message: str) -> None:
        """Log a success message."""
        self.stdout.write(self.style.SUCCESS(message))

    def log_warning(self, message: str) -> None:
        """Log a warning message."""
        self.stdout.write(self.style.WARNING(message))

    def log_error(self, message: str) -> None:
        """Log an error message."""
        self.stdout.write(self.style.ERROR(message))
