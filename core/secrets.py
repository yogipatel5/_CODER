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
            for group in ["django", "database", "redis", "celery", "notion", "logfire", "proxmox"]:
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
                    if secrets:
                        logger.debug(f"\n{group}:")
                        for key in secrets.keys():
                            logger.debug(f"  - {key}")
                logger.debug("\n")
                self._printed_secrets = True

        except Exception as e:
            logger.error(f"Error reading settings from Vault: {e}")

    def get_secret(self, group: str, key: str) -> Optional[str]:
        """Get a specific secret value."""
        return self._secrets.get(group, {}).get(key)

    def get_secrets_group(self, group: str) -> Dict[str, Any]:
        """Get all secrets for a group."""
        return self._secrets.get(group, {})


# Create a singleton instance
secrets_manager = SecretsManager()
