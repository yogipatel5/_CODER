"""Service for managing LXC containers in Proxmox."""

import logging
from typing import Dict, List, Optional

from network.proxmox.api.lxc import LXCAPI

logger = logging.getLogger(__name__)


class LXCService:
    """Service for managing LXC containers."""

    def __init__(self):
        """Initialize LXC service with LXC API client."""
        self.api = LXCAPI()

    def list_containers(self, node: str = "pve") -> List[Dict]:
        """List all LXC containers on a node.

        Args:
            node: Name of the Proxmox node (default: "pve")

        Returns:
            List of container dictionaries with their configurations
        """
        try:
            containers = self.api.list_containers(node=node)
            logger.info(f"Found {len(containers)} LXC containers on node {node}")
            return containers
        except Exception as e:
            logger.error(f"Failed to list containers on node {node}: {str(e)}")
            raise

    def create_container(
        self,
        vmid: int,
        ostemplate: str,
        hostname: str,
        storage: str,
        password: str,
        node: str = "pve",
        memory: int = 512,
        swap: int = 512,
        cores: int = 1,
        **kwargs,
    ) -> Dict:
        """Create a new LXC container.

        Args:
            vmid: VM ID for the new container
            ostemplate: Template to use for container creation
            hostname: Hostname for the container
            storage: Storage location for container
            password: Root password for container
            node: Name of the Proxmox node (default: "pve")
            memory: RAM in MB (default: 512)
            swap: Swap in MB (default: 512)
            cores: Number of CPU cores (default: 1)
            **kwargs: Additional container configuration options

        Returns:
            Response dictionary from Proxmox API
        """
        try:
            result = self.api.create_container(
                vmid=vmid,
                ostemplate=ostemplate,
                hostname=hostname,
                storage=storage,
                password=password,
                node=node,
                memory=memory,
                swap=swap,
                cores=cores,
                **kwargs,
            )
            logger.info(f"Successfully initiated container creation. Task: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to create container {vmid} on node {node}: {str(e)}")
            raise

    def get_container_status(self, node: str, vmid: int) -> Dict:
        """Get current status of a container.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container (e.g., 101 for postgresql)

        Returns:
            Dictionary with container status information
        """
        try:
            status = self.api.get_container_status(node=node, vmid=vmid)
            logger.info(f"Retrieved status for container {vmid} on node {node}")
            return status
        except Exception as e:
            logger.error(f"Failed to get status for container {vmid} on node {node}: {str(e)}")
            raise

    def start_container(self, node: str, vmid: int) -> Dict:
        """Start a container.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container (e.g., 101 for postgresql)

        Returns:
            Dictionary with start task information
        """
        try:
            result = self.api.start_container(node=node, vmid=vmid)
            logger.info(f"Started container {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to start container {vmid} on node {node}: {str(e)}")
            raise

    def stop_container(self, node: str, vmid: int) -> Dict:
        """Stop a container immediately.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container (e.g., 101 for postgresql)

        Returns:
            Dictionary with stop task information
        """
        try:
            result = self.api.stop_container(node=node, vmid=vmid)
            logger.info(f"Stopped container {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to stop container {vmid} on node {node}: {str(e)}")
            raise

    def shutdown_container(self, node: str, vmid: int, timeout: Optional[int] = None) -> Dict:
        """Shutdown a container gracefully.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container
            timeout: Optional timeout in seconds

        Returns:
            Dictionary with shutdown task information
        """
        return self.api.shutdown_container(node=node, vmid=vmid, timeout=timeout)

    def delete_container(self, node: str, vmid: int, force: bool = False) -> Dict:
        """Delete a container.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container
            force: If True, force destroy the container even if running (default: False)

        Returns:
            Dictionary with deletion task information
        """
        return self.api.delete_container(node=node, vmid=vmid, force=force)

    def get_container_logs(self, node: str, vmid: int, limit: int = 500) -> List[str]:
        """Get container logs.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container
            limit: Maximum number of lines to return (default: 500)

        Returns:
            List of log lines
        """
        return self.api.get_container_logs(node=node, vmid=vmid, limit=limit)

    def list_templates(self, node: str = "pve", storage: str = "local") -> List[Dict]:
        """List available LXC templates.

        Args:
            node: Name of the Proxmox node (default: "pve")
            storage: Name of the storage to check (default: "local")

        Returns:
            List of template dictionaries with their information
        """
        try:
            templates = self.api.list_templates(node=node, storage=storage)
            logger.info(f"Found {len(templates)} LXC templates on node {node} in storage {storage}")
            return templates
        except Exception as e:
            logger.error(f"Failed to list templates on node {node} storage {storage}: {str(e)}")
            raise

    def get_next_vmid(self) -> int:
        """Get the next available VM ID.

        Returns:
            Next available VM ID that can be used for container creation
        """
        try:
            vmid = self.api.get_next_vmid()
            logger.info(f"Retrieved next available VM ID: {vmid}")
            return vmid
        except Exception as e:
            logger.error(f"Failed to get next VM ID: {str(e)}")
            raise

    def exec_command(
        self, node: str, vmid: int, command: str, args: List[str] = None, poll: bool = True, poll_interval: int = 2
    ) -> Dict:
        """Execute a command inside a container and optionally wait for completion.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container
            command: Command to execute inside the container
            args: List of command arguments (default: None)
            poll: Whether to poll until task completion (default: True)
            poll_interval: Seconds between poll attempts (default: 2)

        Returns:
            Dictionary with command execution task information
        """
        try:
            response = self.api.exec_command(
                node=node, vmid=vmid, command=command, args=args, poll=poll, poll_interval=poll_interval
            )
            logger.info(f"Command execution completed in container {vmid} on node {node}")
            return response
        except Exception as e:
            logger.error(f"Failed to execute command in container {vmid} on node {node}: {str(e)}")
            raise
