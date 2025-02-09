"""Manages secrets and environment variables for the application."""

import logging
import os
from typing import Any, Dict, Optional

from projects.vault.services.vault_service import VaultService

logger = logging.getLogger(__name__)


class SecretsManager:
    """Manages secrets and environment variables for the application."""

    def __init__(self):
        self.vault_service = VaultService()
        self._secrets: Dict[str, Dict[str, Any]] = {}
        self._printed_secrets = False

    def load_secrets(self, env: Optional[str] = None) -> None:
        """Load all secrets from vault and set environment variables."""
        if not env:
            env = os.getenv("ENV_NAME", "dev")

        try:
            # Get all secrets for the environment
            for group in [
                "django",
                "database",
                "redis",
                "celery",
                "notion",
                "logfire",
                "proxmox",
                "deepseek",
                "pfsense",
                "twilio_yp",
            ]:
                value = self.vault_service.read_secret(env, group)
                if value:
                    self._secrets[group] = value
                    # Automatically set environment variables for all secrets
                    for key, val in value.items():
                        env_var = f"{group.upper()}_{key.upper()}"
                        os.environ[env_var] = str(val)
                        # logger.debug(f"Set environment variable: {env_var}")
                else:
                    logger.warning(f"No {group} settings found in Vault for {env} environment")

            # Print available secrets in dev environment (only once)
            if env == "dev" and not self._printed_secrets:
                logger.debug("\nAvailable Secrets:")
                logger.debug("------------------")
                for group, secrets in self._secrets.items():
                    logger.debug(f"\n{group}:")
                    for key in secrets.keys():
                        logger.debug(f"  - {key}")
                self._printed_secrets = True

        except Exception as e:
            logger.error(f"Error loading secrets: {e}")

    # def get_secret(self, key: str) -> Optional[str]:
    #     """Get a secret by its key.

    #     Args:
    #         key: The key in format 'GROUP_NAME' or 'GROUP_KEY'

    #     Returns:
    #         The secret value or None if not found
    #     """
    #     if "_" not in key:
    #         return None

    #     group, key = key.lower().split("_", 1)
    #     if group not in self._secrets:
    #         return None

    #     return self._secrets[group].get(key)

    def get_secret(self, group: str, key: str) -> Optional[str]:
        """Get a specific secret value."""
        return self._secrets.get(group, {}).get(key)

    def get_secrets_group(self, group: str) -> Dict[str, Any]:
        """Get all secrets for a group."""
        return self._secrets.get(group, {})


# Create a singleton instance
secrets_manager = SecretsManager()
