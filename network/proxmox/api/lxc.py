"""API module for LXC container operations in Proxmox."""

import logging
import os
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

    def get_container_config(self, node: str, vmid: int) -> Dict:
        """Get container configuration.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container

        Returns:
            Dictionary with container configuration information
        """
        try:
            config = self.client.nodes(node).lxc(vmid).config.get()
            logger.info(f"Retrieved config for container {vmid} on node {node}")
            return config
        except Exception as e:
            logger.error(f"Failed to get config for container {vmid} on node {node}: {str(e)}")
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

    def stop_container(self, vmid: int) -> None:
        """Stop a container.

        Args:
            vmid: ID of the container
        """
        try:
            # Get the node where the container is running
            nodes = self.client.nodes.get()
            if not nodes:
                raise ValueError("No nodes found")
            node = self.client.nodes(nodes[0]["node"])

            container = node.lxc(vmid)
            container.status.stop.post()
        except Exception as e:
            logger.error(f"Failed to stop container {vmid}: {str(e)}")
            raise

    def restart_container(self, vmid: int) -> None:
        """Restart a container.

        Args:
            vmid: ID of the container
        """
        try:
            # Get the node where the container is running
            nodes = self.client.nodes.get()
            if not nodes:
                raise ValueError("No nodes found")
            node = self.client.nodes(nodes[0]["node"])

            container = node.lxc(vmid)
            container.status.restart.post()
        except Exception as e:
            logger.error(f"Failed to restart container {vmid}: {str(e)}")
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
                    self.stop_container(vmid)
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

    def list_templates(self, node: str = "pve", storage: str = "local") -> List[Dict]:
        """List available LXC templates.

        Args:
            node: Name of the Proxmox node (default: "pve")
            storage: Name of the storage to check (default: "local")

        Returns:
            List of template dictionaries with their information
        """
        try:
            templates = self.client.nodes(node).storage(storage).content.get(content="vztmpl")
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
            vmid = self.client.cluster.nextid.get()
            logger.info(f"Retrieved next available VM ID: {vmid}")
            return int(vmid)
        except Exception as e:
            logger.error(f"Failed to get next VM ID: {str(e)}")
            raise

    def exec_command(
        self, node: str, vmid: int, command: str, args: List[str] = None, poll: bool = True, poll_interval: int = 2
    ) -> Dict:
        """Execute a command inside a container using SSH.

        Args:
            node: Name of the Proxmox node
            vmid: VM ID of the container
            command: Command to execute inside the container
            args: List of command arguments (default: None)
            poll: Whether to poll until task completion (default: True)
            poll_interval: Seconds between poll attempts (default: 2)

        Returns:
            Dictionary with command output and status
        """
        try:
            # Ensure args is a list
            if args is None:
                args = []

            # Get Proxmox host from getenvment
            proxmox_host = os.getenv("PROXMOX_HOST")
            if not proxmox_host:
                raise Exception("PROXMOX_HOST getenvment variable not set")

            # Extract hostname without port
            proxmox_hostname = proxmox_host.split(":")[0]
            if not proxmox_hostname:
                raise Exception("Failed to extract hostname from PROXMOX_HOST")

            # Construct the command
            full_command = [command] + args if args else [command]
            command_str = " ".join(f"'{arg}'" for arg in full_command)

            # Create a shell script that will be executed on the remote host
            script = f"""#!/bin/bash
set -e
exec 2>&1

# Check container status
echo "=== Container Status ==="
pct status {vmid}
status=$?
if [ $status -ne 0 ]; then
    echo "Container is not running"
    exit 1
fi

# Execute command
echo "=== Command Output ==="
pct exec {vmid} -t -- {command_str}
"""

            logger.info(f"Executing command '{command}' with args {args} in container {vmid} on node {node}")
            logger.info(f"Remote script: {script}")

            # Execute command via SSH
            import subprocess

            ssh_command = ["ssh", "-tt", f"root@{proxmox_hostname}", "bash -s"]
            logger.info(f"Running SSH command: {' '.join(ssh_command)}")

            try:
                result = subprocess.run(ssh_command, input=script, capture_output=True, text=True, check=True)
                logger.info(f"Command output: {result.stdout}")
                if result.stderr:
                    logger.warning(f"Command stderr: {result.stderr}")

                # Print debug info
                logger.debug("Command result:")
                logger.debug(f"  Return code: {result.returncode}")
                logger.debug(f"  Stdout: {repr(result.stdout)}")
                logger.debug(f"  Stderr: {repr(result.stderr)}")

                # Extract command output (everything after "=== Command Output ===")
                output_lines = result.stdout.split("\n")
                command_output = []
                in_command_output = False
                for line in output_lines:
                    if line == "=== Command Output ===":
                        in_command_output = True
                    elif in_command_output:
                        command_output.append(line)

                return {
                    "status": "success",
                    "output": "\n".join(command_output),
                    "error": result.stderr if result.stderr else None,
                }
            except subprocess.CalledProcessError as e:
                logger.error(f"Command failed with exit code {e.returncode}")
                logger.error(f"Command stdout: {e.stdout}")
                logger.error(f"Command stderr: {e.stderr}")
                raise Exception(f"Command failed: {e.stderr}")

        except Exception as e:
            logger.error(f"Failed to execute command in container {vmid} on node {node}: {str(e)}")
            raise

    def configure_network(self, vmid: int, net0: str = "name=eth0,bridge=vmbr0,ip=dhcp") -> None:
        """Configure network interface for LXC container.

        Args:
            vmid: ID of the container
            net0: Network interface configuration string
                 Format: name=<name>,bridge=<bridge>,ip=<ip>
                 Example: name=eth0,bridge=vmbr0,ip=dhcp
        """
        try:
            # Get the node where the container is running
            nodes = self.client.nodes.get()
            if not nodes:
                raise ValueError("No nodes found")
            node = self.client.nodes(nodes[0]["node"])

            container = node.lxc(vmid)
            container.config.put(net0=net0)
        except Exception as e:
            logger.error(f"Failed to configure network for container {vmid}: {str(e)}")
            raise
