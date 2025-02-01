"""
Proxmox API client implementation.
"""

import logging
import os
import time
from typing import Optional

from proxmoxer import ProxmoxAPI

logger = logging.getLogger(__name__)


def setup_django():
    """Setup Django environment to load secrets."""
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()

    # Import and load secrets after Django is setup
    from core.secrets import secrets_manager

    secrets_manager.load_secrets()


class ProxmoxClient:
    """Client for interacting with Proxmox API."""

    def __init__(self):
        """Initialize Proxmox client with credentials from settings."""
        self.host = os.getenv("PROXMOX_HOST")
        self.port = os.getenv("PROXMOX_PORT", "8006")
        self.user = os.getenv("PROXMOX_USER")
        self.token_name = os.getenv("PROXMOX_TOKEN_NAME")
        self.token_secret = os.getenv("PROXMOX_TOKEN_SECRET")

        # Validate required environment variables
        required_vars = {
            "PROXMOX_HOST": self.host,
            "PROXMOX_USER": self.user,
            "PROXMOX_TOKEN_NAME": self.token_name,
            "PROXMOX_TOKEN_SECRET": self.token_secret,
        }

        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        self._client: Optional[ProxmoxAPI] = None

    @property
    def client(self) -> ProxmoxAPI:
        """Get or create Proxmox API client."""
        if self._client is None:
            logger.info("Attempting to create Proxmox client")

            logger.info(f"Using Proxmox host: {self.host}")
            logger.info(f"Using user: {self.user}")
            logger.info(f"Using token name: {self.token_name}")
            logger.debug(f"Token secret present: {'yes' if self.token_secret else 'no'}")

            # Create API token auth string
            token = f"{self.token_name}={self.token_secret}"

            self._client = ProxmoxAPI(
                host=self.host,
                user=self.user,
                token_name=self.token_name,
                token_value=self.token_secret,
                verify_ssl=False,  # Note: In production, this should be True with proper SSL cert
                port=int(self.port),
                timeout=30,  # Increase timeout to 30 seconds
            )
            logger.info("Successfully created Proxmox client instance")
        return self._client

    def test_connection(self) -> bool:
        """Test the connection to Proxmox server.

        Returns:
            bool: True if connection is successful, False otherwise
        """
        try:
            logger.info("Testing Proxmox connection...")
            # Try to get nodes list as a simple test
            nodes = self.client.nodes.get()
            logger.info(f"Successfully connected to Proxmox. Found {len(nodes)} nodes.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Proxmox: {str(e)}")
            return False

    def get_node_info(self, node: str, vmid: int, command: str = None) -> dict:
        """Get information about a specific node and container status.

        Args:
            node (str): Node name
            vmid (int): LXC container ID
            command (str, optional): Not used, kept for backward compatibility

        Returns:
            dict: Container status information
        """
        try:
            logger.info(f"Getting status for LXC {vmid} on node {node}")
            result = self.client.nodes(node).lxc(vmid).status.current.get()
            return result
        except Exception as e:
            logger.error(f"Failed to get container status: {str(e)}")
            raise

    def list_lxc(self, node: str) -> list:
        """List all LXC containers in a node.

        Args:
            node (str): Node name

        Returns:
            list: List of LXC containers
        """
        try:
            logger.info(f"Listing LXC containers on node {node}")
            result = self.client.nodes(node).lxc.get()
            return result
        except Exception as e:
            logger.error(f"Failed to list LXC containers: {str(e)}")
            raise

    def get_container_config(self, node: str, vmid: int) -> dict:
        """Get container configuration.

        Args:
            node (str): Node name
            vmid (int): LXC container ID

        Returns:
            dict: Container configuration
        """
        try:
            logger.info(f"Getting config for LXC {vmid} on node {node}")
            result = self.client.nodes(node).lxc(vmid).config.get()
            return result
        except Exception as e:
            logger.error(f"Failed to get config: {str(e)}")
            raise

    def get_container_features(self, node: str, vmid: int) -> dict:
        """Get container features.

        Args:
            node (str): Node name
            vmid (int): LXC container ID

        Returns:
            dict: Container features
        """
        try:
            logger.info(f"Getting features for LXC {vmid} on node {node}")
            result = self.client.nodes(node).lxc(vmid).feature.get()
            return result
        except Exception as e:
            logger.error(f"Failed to get features: {str(e)}")
            raise

    def execute_command(self, node: str, vmid: int, command: str, args: str = None, timeout: int = 30) -> dict:
        """Execute a command in an LXC container and wait for completion.

        Args:
            node (str): Node name
            vmid (int): LXC container ID
            command (str): Command to execute
            args (str, optional): Command arguments. Defaults to None.
            timeout (int, optional): Maximum time to wait for command completion in seconds. Defaults to 30.

        Returns:
            dict: Command execution result
        """
        try:
            logger.info(f"Executing command {command} with args {args} in LXC {vmid} on node {node}")

            # Execute the command using the API path directly
            result = self.client.get(f"/nodes/{node}/lxc/{vmid}/exec", {"command": command, "args": args or ""})

            # Get the UPID (Unique Process ID)
            upid = result
            logger.info(f"Job initiated with UPID: {upid}")

            # Monitor the job until completion or timeout
            start_time = time.time()
            while True:
                # Check if we've exceeded timeout
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Command execution timed out after {timeout} seconds")

                # Check the status of the task
                job_status = self.client.nodes(node).tasks(upid).status.get()
                status = job_status.get("status")
                logger.info(f"Current job status: {status}")

                # If the task has finished, return the result
                if status in ["stopped", "OK"]:
                    return job_status
                elif status == "error":
                    raise Exception(f"Command execution failed: {job_status}")

                # Wait before checking again
                time.sleep(2)

        except Exception as e:
            logger.error(f"Failed to execute command: {str(e)}")
            raise


if __name__ == "__main__":
    # Setup Django to load secrets
    setup_django()

    try:
        # Initialize client
        client = ProxmoxClient()

        # Test connection
        if client.test_connection():
            try:
                # First list containers
                containers = client.list_lxc("pve")
                print("\nAvailable LXC containers:")
                for container in containers:
                    print(
                        f"ID: {container.get('vmid')}, Name: {container.get('name')}, Status: {container.get('status')}"
                    )

                print("\nExecuting 'ls' command in litellm-proxy container...")
                # Execute ls command in container 114 (litellm-proxy)
                result = client.execute_command("pve", 114, "ls", timeout=10)
                print(f"Command result: {result}")
            except Exception as e:
                print(f"Error: {str(e)}")
        else:
            print("Failed to connect to Proxmox")
    except ValueError as e:
        print(f"Error: {str(e)}")
