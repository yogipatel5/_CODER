import logging

from django.core.management.base import BaseCommand

from projects.vault.services.vault_service import VaultService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to read secrets from Vault."""

    help = "Read a secret from Vault"

    def add_arguments(self, parser):
        parser.add_argument(
            "--env",
            type=str,
            choices=["dev", "prod"],
            required=True,
            help="Environment to read secret from (dev/prod)",
        )
        parser.add_argument(
            "--name",
            type=str,
            required=True,
            help="Name of the secret",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Increase output verbosity",
        )

    def handle(self, *args, **options):
        if options["verbose"]:
            logger.setLevel(logging.DEBUG)

        try:
            env = options["env"]
            name = options["name"]

            vault_service = VaultService()
            secret = vault_service.read_secret(env=env, name=name)

            if secret:
                self.stdout.write(self.style.SUCCESS(f"Secret '{name}' from {env} environment:\n{secret}"))
            else:
                self.stderr.write(self.style.ERROR(f"Failed to read secret '{name}' from {env} environment"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))
