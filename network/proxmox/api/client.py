"""
Proxmox API client implementation.
"""

import logging
from typing import Optional

from django.conf import settings
from proxmoxer import ProxmoxAPI

logger = logging.getLogger(__name__)


class ProxmoxClient:
    """Client for interacting with Proxmox API."""

    def __init__(self):
        """Initialize Proxmox client with credentials from settings."""
        self.proxmox_creds = settings.PROXMOX_CREDS
        self._client: Optional[ProxmoxAPI] = None

    @property
    def client(self) -> ProxmoxAPI:
        """Get or create Proxmox API client."""
        if self._client is None:
            logger.info("Attempting to create Proxmox client")
            logger.debug(f"Proxmox credentials from settings: {self.proxmox_creds}")

            host = self.proxmox_creds.get("HOST", "").replace("https://", "")  # Remove https:// if present
            token_id = self.proxmox_creds.get("TOKEN_ID")
            token_secret = self.proxmox_creds.get("TOKEN_SECRET")

            # Split token_id into user and tokenid parts
            if "@" in token_id and "!" in token_id:
                user_realm, tokenid = token_id.split("!")
                token_name = tokenid  # Use only the token part after !
                user = user_realm  # Keep the user@realm part
            else:
                logger.error(f"Invalid token ID format. Expected format: USER@REALM!TOKENID, got: {token_id}")
                raise ValueError("Invalid token ID format")

            logger.info(f"Using Proxmox host: {host}")
            logger.info(f"Using user: {user}")
            logger.info(f"Using token name: {token_name}")
            logger.debug(f"Token secret present: {'yes' if token_secret else 'no'}")

            self._client = ProxmoxAPI(
                host=host,
                user=user,  # Pass user@realm separately
                token_name=token_name,  # Pass only the token name part
                token_value=token_secret,
                verify_ssl=False,  # Note: In production, this should be True with proper SSL cert
                port=8006,
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
