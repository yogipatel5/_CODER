"""API module for LXC container operations in Proxmox."""

import logging
from typing import Dict, List, Optional

from network.proxmox.api.client import ProxmoxClient

logger = logging.getLogger(__name__)


class LXCAPI:
    """API class for LXC container operations."""

    def __init__(self):
        """Initialize LXC API with Proxmox client."""
        self.client = ProxmoxClient().client

    def list_containers(self, node: str = "pve") -> List[Dict]:
        """List all LXC containers on a node.

        Args:
            node: Name of the Proxmox node (default: "pve")

        Returns:
            List of container dictionaries with their configurations
        """
        try:
            containers = self.client.nodes(node).lxc.get()
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
            config = {
                "ostemplate": ostemplate,
                "hostname": hostname,
                "storage": storage,
                "password": password,
                "memory": memory,
                "swap": swap,
                "cores": cores,
                **kwargs,
            }
            response = self.client.nodes(node).lxc.create(vmid=vmid, **config)
            logger.info(f"Created LXC container {vmid} on node {node}")
            return response
        except Exception as e:
            logger.error(f"Failed to create container {vmid} on node {node}: {str(e)}")
            raise

    def get_container_status(self, node: str, vmid: int) -> Dict:
        """Get current status of a container.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container

        Returns:
            Dictionary with container status information
        """
        try:
            status = self.client.nodes(node).lxc(vmid).status.current.get()
            logger.info(f"Retrieved status for container {vmid} on node {node}")
            return status
        except Exception as e:
            logger.error(f"Failed to get status for container {vmid} on node {node}: {str(e)}")
            raise

    def start_container(self, node: str, vmid: int) -> Dict:
        """Start a container.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container

        Returns:
            Dictionary with start task information
        """
        try:
            result = self.client.nodes(node).lxc(vmid).status.start.post()
            logger.info(f"Started container {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to start container {vmid} on node {node}: {str(e)}")
            raise

    def stop_container(self, node: str, vmid: int) -> Dict:
        """Stop a container.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container

        Returns:
            Dictionary with stop task information
        """
        try:
            result = self.client.nodes(node).lxc(vmid).status.stop.post()
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
        try:
            params = {"timeout": timeout} if timeout is not None else {}
            result = self.client.nodes(node).lxc(vmid).status.shutdown.post(**params)
            logger.info(f"Initiated shutdown for container {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to shutdown container {vmid} on node {node}: {str(e)}")
            raise

    def delete_container(self, node: str, vmid: int, force: bool = False) -> Dict:
        """Delete a container.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container
            force: If True, force destroy the container even if running (default: False)

        Returns:
            Dictionary with deletion task information
        """
        try:
            if force:
                # Stop the container first if forcing deletion
                try:
                    self.stop_container(node, vmid)
                except Exception:
                    # Ignore stop errors when force deleting
                    pass

            result = self.client.nodes(node).lxc(vmid).delete()
            logger.info(f"Deleted container {vmid} on node {node}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete container {vmid} on node {node}: {str(e)}")
            raise

    def get_container_logs(self, node: str, vmid: int, limit: int = 500) -> List[str]:
        """Get container logs.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container
            limit: Maximum number of lines to return (default: 500)

        Returns:
            List of log lines
        """
        try:
            # Get task logs for the container
            tasks = self.client.nodes(node).tasks.get(vmid=vmid, limit=limit)

            # Get system logs for the container
            try:
                syslog = self.client.nodes(node).lxc(vmid).status.current.get()
                if "syslog" in syslog:
                    tasks.extend(syslog["syslog"])
            except Exception as e:
                logger.warning(f"Failed to get syslog for container {vmid}: {str(e)}")

            logger.info(f"Retrieved logs for container {vmid} on node {node}")
            return tasks
        except Exception as e:
            logger.error(f"Failed to get logs for container {vmid} on node {node}: {str(e)}")
            raise
