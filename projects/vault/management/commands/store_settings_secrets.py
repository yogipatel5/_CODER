import logging
import os

from django.core.management.base import BaseCommand

from projects.vault.services.vault_service import VaultService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command to store settings secrets in Vault."""

    help = "Store Django settings secrets in Vault"

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
            required=True,
            help="Environment to store secrets for",
        )

    def handle(self, *args, **options):
        if options["verbose"]:
            logger.setLevel(logging.DEBUG)

        try:
            vault_service = VaultService()
            env = options["env"]

            # Group 1: Django Core Settings
            django_settings = {
                "secret_key": os.getenv("DJANGO_SECRET_KEY"),
                "debug": os.getenv("DJANGO_DEBUG", "True"),
                "allowed_hosts": os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(","),
            }
            vault_service.create_or_update_secret(env, "django", django_settings)
            logger.info("Stored Django core settings in Vault")

            # Group 2: Database Settings
            db_settings = {
                "name": os.getenv("POSTGRES_DB", ""),
                "user": os.getenv("POSTGRES_USER", ""),
                "password": os.getenv("POSTGRES_PASSWORD", ""),
                "host": os.getenv("POSTGRES_HOST", ""),
                "port": os.getenv("POSTGRES_PORT", ""),
            }
            vault_service.create_or_update_secret(env, "database", db_settings)
            logger.info("Stored database settings in Vault")

            # Group 3: Redis Settings
            redis_settings = {
                "host": os.getenv("REDIS_HOST", ""),
                "port": os.getenv("REDIS_PORT", ""),
            }
            vault_service.create_or_update_secret(env, "redis", redis_settings)
            logger.info("Stored Redis settings in Vault")

            # Group 4: Celery Settings
            celery_settings = {
                "broker_url": os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
                "result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0"),
                "timezone": "America/New_York",
            }
            vault_service.create_or_update_secret(env, "celery", celery_settings)
            logger.info("Stored Celery settings in Vault")

            # Group 5: Logfire Settings
            logfire_settings = {
                "token": os.getenv("LOGFIRE_TOKEN", "VKB9cfmnDYRp1n5dGh362g5CmYwhrGgSnFgD5YkK5T6x"),
                "project": "coder",
            }
            vault_service.create_or_update_secret(env, "logfire", logfire_settings)
            logger.info("Stored Logfire settings in Vault")

            self.stdout.write(
                self.style.SUCCESS(f"Successfully stored all settings secrets in Vault for {env} environment")
            )

        except Exception as e:
            logger.error(f"Failed to store secrets in Vault: {e}")
            self.stdout.write(self.style.ERROR(f"Failed to store secrets in Vault: {e}"))
