import logging

from django.core.management.base import BaseCommand

from core.config import get_project_name
from projects.vault.api.client import VaultClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to set up Vault policies and tokens."""

    help = "Set up Vault policies and tokens for different environments"

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
            client = VaultClient()
            project_name = get_project_name()

            # Define policies for KV v2
            prod_policy = f"""
                # Allow management of {project_name}/* path
                path "{project_name}/data/prod/*" {{
                    capabilities = ["create", "read", "update", "delete", "list"]
                }}
                path "{project_name}/data/dev/*" {{
                    capabilities = ["create", "read", "update", "delete", "list"]
                }}
                path "{project_name}/metadata/prod/*" {{
                    capabilities = ["list"]
                }}
                path "{project_name}/metadata/dev/*" {{
                    capabilities = ["list"]
                }}
            """

            dev_policy = f"""
                # Allow read-only access to {project_name}/dev/* path
                path "{project_name}/data/dev/*" {{
                    capabilities = ["create", "read", "update", "delete", "list"]
                }}
                path "{project_name}/metadata/dev/*" {{
                    capabilities = ["list"]
                }}
            """

            # Create policies
            try:
                client.client.sys.create_or_update_policy(
                    name=f"{project_name}-prod",
                    policy=prod_policy,
                )
                self.stdout.write(self.style.SUCCESS(f"Created {project_name}-prod policy"))

                client.client.sys.create_or_update_policy(
                    name=f"{project_name}-dev",
                    policy=dev_policy,
                )
                self.stdout.write(self.style.SUCCESS(f"Created {project_name}-dev policy"))

                # Create tokens with policies
                dev_token = client.client.auth.token.create(
                    policies=[f"{project_name}-dev"],
                    ttl="720h",  # 30 days
                )
                prod_token = client.client.auth.token.create(
                    policies=[f"{project_name}-prod"],
                    ttl="720h",  # 30 days
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        "\nCreated tokens:\n"
                        f"DEV_TOKEN={dev_token['auth']['client_token']}\n"
                        f"PROD_TOKEN={prod_token['auth']['client_token']}"
                    )
                )

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Failed to create policies: {str(e)}"))
                return

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))
