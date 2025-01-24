import json
import logging

from django.core.management.base import BaseCommand

from projects.vault.services.vault_service import VaultService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to add secrets to Vault."""

    help = "Add a secret to Vault"

    def add_arguments(self, parser):
        parser.add_argument(
            "--env",
            type=str,
            choices=["dev", "prod"],
            required=True,
            help="Environment to add secret to (dev/prod)",
        )
        parser.add_argument(
            "--name",
            type=str,
            required=True,
            help="Name of the secret",
        )
        parser.add_argument(
            "--value",
            type=str,
            required=True,
            help="Value of the secret. Can be a JSON string for complex values",
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
            value = options["value"]

            # Try to parse value as JSON if it's a complex value
            try:
                parsed_value = json.loads(value)
                logger.debug("Parsed value as JSON")
            except json.JSONDecodeError:
                parsed_value = value
                logger.debug("Using value as string")

            vault_service = VaultService()
            success = vault_service.create_or_update_secret(
                env=env,
                name=name,
                value={"value": parsed_value},
            )

            if success:
                self.stdout.write(self.style.SUCCESS(f"Successfully added secret '{name}' to {env} environment"))
            else:
                self.stderr.write(self.style.ERROR(f"Failed to add secret '{name}' to {env} environment"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))
