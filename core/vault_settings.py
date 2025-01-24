import logging
import os
from typing import Any, Dict, Optional

from projects.vault.services.vault_service import VaultService

logger = logging.getLogger(__name__)


def get_vault_settings(env: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Get settings from Vault for the specified environment.

    Args:
        env: Environment to get settings for. If not specified, will try to get from ENV_NAME env var
             or default to 'dev'

    Returns:
        Dictionary of settings from Vault
    """
    if not env:
        env = os.getenv("ENV_NAME", "dev")

    vault_service = VaultService()
    settings = {}

    # List of settings groups to fetch
    groups = ["django", "database", "redis", "celery", "logfire"]

    for group in groups:
        try:
            value = vault_service.read_secret(env, group)
            if value:
                settings[group] = value
            else:
                logger.warning(f"No {group} settings found in Vault for {env} environment")
        except Exception as e:
            logger.error(f"Error reading {group} settings from Vault: {e}")
            settings[group] = {}

    return settings
