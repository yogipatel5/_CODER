import logging
from typing import Dict, List, Optional

from core.config import get_project_name
from projects.vault.api.client import VaultClient

logger = logging.getLogger(__name__)


class VaultService:
    """Service layer for Vault operations."""

    def __init__(self, client: Optional[VaultClient] = None):
        self.client = client or VaultClient()
        self.mount_point = get_project_name()

    def create_secret_engine(self, environments: List[str]) -> Optional[Dict[str, str]]:
        """
        Create a new KV version 2 secret engine for the project.

        Args:
            environments: List of environments to create paths for (e.g., ['dev', 'prod'])

        Returns:
            Dictionary of environment paths created or None if failed
        """
        logger.info(f"Creating secret engine for project: {self.mount_point} with environments: {environments}")

        base_path = self.mount_point
        env_paths = {}

        try:
            # Enable the KV version 2 secrets engine
            self.client.enable_kv_engine(base_path)

            # Create paths for each environment
            for env in environments:
                env_path = f"{base_path}/{env}"
                env_paths[env] = env_path

                # Initialize the environment path with metadata
                self.client.client.secrets.kv.v2.create_or_update_secret(
                    path=f"{env}/metadata",  # Changed path to include environment
                    secret={"initialized": True},
                    mount_point=base_path,  # Use base_path as mount_point instead of env_path
                )
                logger.info(f"Initialized environment path: {env_path}")

            return env_paths

        except Exception as e:
            logger.error(f"Error creating secret engine: {e}")
            return None

    def list_secrets(self, path: str = "") -> Dict[str, List[str]]:
        """
        List all secrets in the vault for all environments.

        Args:
            path: Base path to list secrets from

        Returns:
            Dictionary of environments and their secrets
        """
        logger.info("Listing secrets from vault")
        secrets_by_env = {}

        try:
            # List mounted secret engines
            mounted_secrets = self.client.list_mounted_engines()

            for mount_point, details in mounted_secrets.items():
                if not isinstance(details, dict):
                    continue

                if details.get("type") == "kv":
                    mount_path = mount_point.rstrip("/")
                    try:
                        secrets = self.client.client.secrets.kv.v2.list_secrets(
                            path="",
                            mount_point=mount_path,
                        )
                        secrets_by_env[mount_path] = secrets.get("data", {}).get("keys", [])
                        logger.info(f"Found secrets in {mount_path}: {secrets}")
                    except Exception as e:
                        logger.error(f"Error listing secrets at {mount_path}: {e}")
                        secrets_by_env[mount_path] = []

            return secrets_by_env

        except Exception as e:
            logger.error(f"Error listing secrets: {e}")
            return {"error": str(e)}

    def create_or_update_secret(self, env: str, name: str, value: Dict) -> bool:
        """
        Create or update a secret in the specified environment.

        Args:
            env: Environment (dev/prod)
            name: Secret name
            value: Secret value

        Returns:
            True if successful, False otherwise
        """
        try:
            # For KV v2, the path structure is: mount_point/data/<path>
            # In our case: coder/data/env/name
            self.client.client.secrets.kv.v2.create_or_update_secret(
                path=f"{env}/{name}",  # Path under data/
                secret=value,
                mount_point=self.mount_point,
            )
            logger.info(f"Created/updated secret {name} in {self.mount_point}/{env}")
            return True
        except Exception as e:
            logger.error(f"Error creating/updating secret: {e}")
            return False

    def read_secret(self, env: str, name: str) -> Optional[Dict]:
        """
        Read a secret from the specified environment.

        Args:
            env: Environment (dev/prod)
            name: Secret name

        Returns:
            Secret value or None if not found
        """
        try:
            # For KV v2, the path structure is: mount_point/data/<path>
            # In our case: coder/data/env/name
            secret = self.client.client.secrets.kv.v2.read_secret_version(
                path=f"{env}/{name}",  # Path under data/
                mount_point=self.mount_point,
            )
            return secret.get("data", {}).get("data")
        except Exception as e:
            logger.error(f"Error reading secret: {e}")
            return None
