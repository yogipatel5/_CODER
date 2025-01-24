"""Django management command to set up initial secrets in Vault."""
import logging
import os

from django.core.management.base import BaseCommand

from projects.vault.services.vault_service import VaultService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to set up initial secrets in Vault."""

    help = "Set up initial secrets in Vault"

    def add_arguments(self, parser):
        parser.add_argument(
            "--env",
            type=str,
            default="dev",
            help="Environment to set up secrets for (dev/prod)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Increase output verbosity",
        )

    def handle(self, *args, **options):
        if options["verbose"]:
            logger.setLevel(logging.DEBUG)

        env = options["env"]
        try:
            vault_service = VaultService()

            # Django secrets
            django_secrets = {
                "SECRET_KEY": os.getenv(
                    "DJANGO_SECRET_KEY",
                    "django-insecure-6_+=dtw-cnix4njfi6hiv1r0ar@#mbk09frbjp+ee7c7sov=ua",
                ),
            }
            vault_service.create_or_update_secret(env, "django", django_secrets)
            self.stdout.write(self.style.SUCCESS("Added Django secrets"))

            # Logfire secrets
            logfire_secrets = {
                "LOGFIRE_TOKEN": os.getenv(
                    "LOGFIRE_TOKEN", "VKB9cfmnDYRp1n5dGh362g5CmYwhrGgSnFgD5YkK5T6x"
                ),
            }
            vault_service.create_or_update_secret(env, "logfire", logfire_secrets)
            self.stdout.write(self.style.SUCCESS("Added Logfire secrets"))

            # Notion secrets
            notion_secrets = {
                "NOTION_API_KEY": os.getenv("NOTION_API_KEY", ""),
            }
            vault_service.create_or_update_secret(env, "notion", notion_secrets)
            self.stdout.write(self.style.SUCCESS("Added Notion secrets"))

            # Postgres secrets
            postgres_secrets = {
                "POSTGRES_DB": os.getenv("POSTGRES_DB", "coder"),
                "POSTGRES_USER": os.getenv("POSTGRES_USER", "postgres"),
                "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "postgres"),
                "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "localhost"),
                "POSTGRES_PORT": os.getenv("POSTGRES_PORT", "5432"),
            }
            vault_service.create_or_update_secret(env, "postgres", postgres_secrets)
            self.stdout.write(self.style.SUCCESS("Added Postgres secrets"))

            # Redis secrets
            redis_secrets = {
                "REDIS_HOST": os.getenv("REDIS_HOST", "localhost"),
                "REDIS_PORT": os.getenv("REDIS_PORT", "6379"),
            }
            vault_service.create_or_update_secret(env, "redis", redis_secrets)
            self.stdout.write(self.style.SUCCESS("Added Redis secrets"))

            # Celery secrets
            celery_secrets = {
                "CELERY_BROKER_URL": os.getenv(
                    "CELERY_BROKER_URL", "redis://redis:6379/0"
                ),
                "CELERY_RESULT_BACKEND": os.getenv(
                    "CELERY_RESULT_BACKEND", "redis://redis:6379/0"
                ),
            }
            vault_service.create_or_update_secret(env, "celery", celery_secrets)
            self.stdout.write(self.style.SUCCESS("Added Celery secrets"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error: {str(e)}"))
