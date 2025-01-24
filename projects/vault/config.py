"""Helper module to load configuration from Vault."""
import logging
import os
from typing import Dict, Optional

from .services.vault_service import VaultService

logger = logging.getLogger(__name__)


def get_vault_service() -> Optional[VaultService]:
    """Get a configured VaultService instance."""
    try:
        return VaultService()
    except Exception as e:
        logger.error(f"Failed to initialize Vault service: {e}")
        return None


def load_vault_secrets(env: str = None) -> Dict:
    """
    Load secrets from Vault for the specified environment.
    
    Args:
        env: Environment to load secrets for. If None, will try to get from ENV_NAME
             environment variable, defaulting to 'dev'.
    
    Returns:
        Dictionary of secrets loaded from Vault.
    """
    if not env:
        env = os.getenv("ENV_NAME", "dev")
    
    vault_service = get_vault_service()
    if not vault_service:
        logger.warning("Vault service not available, using environment variables")
        return {}
    
    # Load secrets from Vault
    secrets = {}
    secret_keys = [
        "django",  # Contains SECRET_KEY
        "logfire",  # Contains LOGFIRE_TOKEN
        "notion",  # Contains NOTION_API_KEY
        "postgres",  # Contains database credentials
        "redis",  # Contains redis configuration
        "celery",  # Contains celery configuration
    ]
    
    for key in secret_keys:
        try:
            value = vault_service.read_secret(env, key)
            if value:
                secrets.update(value)
        except Exception as e:
            logger.error(f"Failed to read {key} secret from Vault: {e}")
    
    return secrets
