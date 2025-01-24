import logging

from django.core.management.base import BaseCommand

from projects.vault.services.vault_service import VaultService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to initialize Vault secret engines."""

    help = "Initialize Vault secret engines"

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Increase output verbosity",
        )

    def handle(self, *args, **options):
        if options["verbose"]:
            logger.setLevel(logging.DEBUG)

        try:
            vault_service = VaultService()
            environments = ["dev", "prod"]

            env_paths = vault_service.create_secret_engine(environments=environments)

            if env_paths:
                self.stdout.write(self.style.SUCCESS(f"Successfully initialized secret engines:\n{env_paths}"))
            else:
                self.stderr.write(self.style.ERROR("Failed to initialize secret engines"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))
