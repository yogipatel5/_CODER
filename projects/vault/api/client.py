import logging
import os

import hvac
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class VaultClient:
    """Client for interacting with HashiCorp Vault."""

    def __init__(self, vault_path=None, vault_token=None):
        self.vault_path = vault_path or os.getenv("VAULT_ADDR")
        self.vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self.client = hvac.Client(url=self.vault_path, token=self.vault_token)

    def enable_kv_engine(self, path, options=None):
        """Enable a KV version 2 secrets engine at the specified path."""
        try:
            self.client.sys.enable_secrets_engine(backend_type="kv", path=path, options=options or {"version": "2"})
            logger.info(f"Created KV store at {path}")
            return True
        except hvac.exceptions.InvalidRequest as e:
            if "path is already in use" in str(e):
                logger.info(f"KV store already exists at {path}")
                return True
            logger.error(f"Failed to enable KV engine at {path}: {e}")
            raise

    def list_mounted_engines(self):
        """List all mounted secret engines."""
        try:
            return self.client.sys.list_mounted_secrets_engines()
        except Exception as e:
            logger.error(f"Error listing mounted secret engines: {e}")
            raise

    def create_or_update_secret(self, path, secret, mount_point):
        """Create or update a secret at the specified path."""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(path=path, secret=secret, mount_point=mount_point)
            return True
        except Exception as e:
            logger.error(f"Failed to create/update secret at {path}: {e}")
            raise

    def list_secrets(self, path="", mount_point=""):
        """List secrets at the specified path."""
        try:
            response = self.client.secrets.kv.v2.list_secrets(path=path, mount_point=mount_point)
            return response.get("data", {}).get("keys", [])
        except Exception as e:
            if "404" in str(e):
                logger.info(f"No secrets found at {mount_point}/{path}")
                return []
            logger.error(f"Error listing secrets at {mount_point}/{path}: {e}")
            raise
