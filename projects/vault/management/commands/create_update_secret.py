import json
import logging
from typing import Dict

from django.core.management.base import BaseCommand, CommandError

from projects.vault.services.vault_service import VaultService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to create or update secrets in Vault.

    Examples:
        # Store at root level (coder/database)
        python manage.py create_update_secret --name database --value '{"user": "admin"}'

        # Store in environment (coder/dev/database)
        python manage.py create_update_secret --env dev --name database --value '{"user": "admin"}'

        # Store in nested path (coder/services/database)
        python manage.py create_update_secret --name services/database --value '{"user": "admin"}'

        # Store from JSON file
        python manage.py create_update_secret --name database --file secrets.json
    """

    help = "Create or update secrets in Vault. Use --env for environment-specific paths or omit for root level."

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Increase output verbosity",
        )
        parser.add_argument(
            "--env",
            type=str,
            choices=["dev", "prod"],
            help="Optional: Environment to store secrets for. If not provided, secret will be stored at root level",
        )
        parser.add_argument(
            "--name",
            type=str,
            required=True,
            help="Name/path of the secret (e.g., 'database', 'django', 'services/database')",
        )
        parser.add_argument(
            "--value",
            type=str,
            help='JSON string of secret value (e.g. \'{"user": "admin", "password": "secret"}\')',
        )
        parser.add_argument(
            "--file",
            type=str,
            help="Path to JSON file containing secret value",
        )

    def handle(self, *args, **options):
        if options["verbose"]:
            logger.setLevel(logging.DEBUG)

        try:
            # Get secret value from either --value or --file
            if options["value"] and options["file"]:
                raise CommandError("Cannot specify both --value and --file")
            elif options["value"]:
                try:
                    secret_value = json.loads(options["value"])
                except json.JSONDecodeError as e:
                    raise CommandError(f"Invalid JSON in --value: {e}")
            elif options["file"]:
                try:
                    with open(options["file"], "r") as f:
                        secret_value = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError) as e:
                    raise CommandError(f"Error reading JSON file: {e}")
            else:
                raise CommandError("Must specify either --value or --file")

            # Validate secret value is a dictionary
            if not isinstance(secret_value, Dict):
                raise CommandError("Secret value must be a JSON object/dictionary")

            # Store secret in Vault
            vault_service = VaultService()

            if options["env"]:
                # Store in environment-specific path
                success = vault_service.create_or_update_secret(
                    env=options["env"],
                    name=options["name"],
                    value=secret_value,
                )
                path = f"{options['env']}/{options['name']}"
            else:
                # Store directly at root level using raw KV v2 API
                success = vault_service.client.client.secrets.kv.v2.create_or_update_secret(
                    path=options["name"],
                    secret=secret_value,
                    mount_point=vault_service.mount_point,
                )
                path = options["name"]
                success = True if success else False

            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully stored secret at path: {vault_service.mount_point}/{path}")
                )
            else:
                raise CommandError("Failed to store secret in Vault")

        except Exception as e:
            logger.error(f"Failed to store secret in Vault: {e}")
            raise CommandError(f"Failed to store secret in Vault: {e}")
