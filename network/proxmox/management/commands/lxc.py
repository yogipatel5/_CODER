"""Management command for LXC container operations."""

import json
import logging

from django.core.management.base import BaseCommand, CommandError

from network.proxmox.services.lxc import LXCService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command for managing LXC containers in Proxmox."""

    help = "Manage LXC containers in Proxmox"

    def add_arguments(self, parser):
        """Add command arguments."""
        subparsers = parser.add_subparsers(dest="action", help="Action to perform")

        # List command
        list_parser = subparsers.add_parser("list", help="List all containers")
        list_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")

        # Templates command
        templates_parser = subparsers.add_parser("templates", help="List available templates")
        templates_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")

        # Next ID command
        subparsers.add_parser("nextid", help="Get next available VM ID")

        # Status command
        status_parser = subparsers.add_parser("status", help="Get container status")
        status_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        status_parser.add_argument("--vmid", type=int, required=True, help="Container ID")

        # Start command
        start_parser = subparsers.add_parser("start", help="Start a container")
        start_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        start_parser.add_argument("--vmid", type=int, required=True, help="Container ID")

        # Stop command
        stop_parser = subparsers.add_parser("stop", help="Stop a container")
        stop_parser.add_argument("--vmid", type=int, required=True, help="Container ID")

        # Restart command
        restart_parser = subparsers.add_parser("restart", help="Restart a container")
        restart_parser.add_argument("--vmid", required=True, type=int, help="ID of the container")

        # Shutdown command
        shutdown_parser = subparsers.add_parser("shutdown", help="Gracefully shutdown a container")
        shutdown_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        shutdown_parser.add_argument("--vmid", type=int, required=True, help="Container ID")
        shutdown_parser.add_argument("--timeout", type=int, help="Shutdown timeout in seconds")

        # Delete command
        delete_parser = subparsers.add_parser("delete", help="Delete a container")
        delete_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        delete_parser.add_argument("--vmid", type=int, required=True, help="Container ID")
        delete_parser.add_argument("--force", action="store_true", help="Force delete container even if running")

        # Logs command
        logs_parser = subparsers.add_parser("logs", help="Get container logs")
        logs_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        logs_parser.add_argument("--vmid", type=int, required=True, help="Container ID")
        logs_parser.add_argument("--limit", type=int, default=500, help="Maximum number of log lines to show")

        # Config command
        config_parser = subparsers.add_parser("config", help="Get container configuration")
        config_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        config_parser.add_argument("--vmid", type=int, required=True, help="Container ID")

        # Create command
        create_parser = subparsers.add_parser("create", help="Create a new container")
        create_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        create_parser.add_argument("--vmid", type=int, required=True, help="Container ID")
        create_parser.add_argument("--ostemplate", required=True, help="OS template for container creation")
        create_parser.add_argument("--hostname", required=True, help="Hostname for new container")
        create_parser.add_argument("--storage", required=True, help="Storage location for new container")
        create_parser.add_argument("--password", required=True, help="Root password for new container")
        create_parser.add_argument("--memory", type=int, default=512, help="RAM in MB for new container")
        create_parser.add_argument("--cores", type=int, default=1, help="CPU cores for new container")
        create_parser.add_argument("--ssh-key-file", help="Path to SSH public key file to inject into container")

        # Exec command
        exec_parser = subparsers.add_parser("exec", help="Execute a command in a container")
        exec_parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        exec_parser.add_argument("--vmid", type=int, required=True, help="Container ID")
        exec_parser.add_argument("--command", required=True, help="Command to execute inside the container")
        exec_parser.add_argument("--args", nargs="*", help="Additional arguments for the command")
        exec_parser.add_argument("--no-poll", action="store_true", help="Don't wait for command completion")
        exec_parser.add_argument("--poll-interval", type=int, default=2, help="Seconds between status checks")

        # Configure network command
        configure_network_parser = subparsers.add_parser(
            "configure-network", help="Configure network interface for LXC container"
        )
        configure_network_parser.add_argument("--vmid", required=True, type=int, help="ID of the container")
        configure_network_parser.add_argument(
            "--net0",
            default="name=eth0,bridge=vmbr0,ip=dhcp",
            help="Network interface configuration string (default: %(default)s)",
        )

    def handle(self, *args, **options):
        """Handle the command."""
        try:
            # Set up logging
            logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            ch.setFormatter(formatter)
            logger.addHandler(ch)

            service = LXCService()
            action = options["action"]

            if action == "list":
                containers = service.list_containers()
                self.stdout.write(json.dumps(containers, indent=2))

            elif action == "templates":
                templates = service.list_templates(node=options["node"])
                self.stdout.write(json.dumps(templates, indent=2))

            elif action == "nextid":
                next_id = service.get_next_vmid()
                self.stdout.write(str(next_id))

            elif action == "create":
                # Extract specific arguments needed for create_container
                create_args = {
                    "node": options["node"],
                    "vmid": options["vmid"],
                    "ostemplate": options["ostemplate"],
                    "hostname": options["hostname"],
                    "storage": options["storage"],
                    "password": options["password"],
                    "memory": options["memory"],
                    "cores": options["cores"],
                }

                # Add SSH key if provided
                if options.get("ssh_key_file"):
                    try:
                        with open(options["ssh_key_file"], "r") as f:
                            ssh_key = f.read().strip()
                        create_args["ssh-public-keys"] = ssh_key
                    except Exception as e:
                        raise CommandError(f"Failed to read SSH key file: {str(e)}")

                response = service.create_container(**create_args)
                self.stdout.write(json.dumps(response, indent=2))

            elif action == "status":
                response = service.get_container_status(node=options["node"], vmid=options["vmid"])
                self.stdout.write(json.dumps(response, indent=2))

            elif action == "start":
                response = service.start_container(node=options["node"], vmid=options["vmid"])
                self.stdout.write(json.dumps(response, indent=2))

            elif action == "stop":
                service.stop_container(options["vmid"])
                self.stdout.write(self.style.SUCCESS(f"Container {options['vmid']} stopped successfully"))

            elif action == "restart":
                service.restart_container(options["vmid"])
                self.stdout.write(self.style.SUCCESS(f"Container {options['vmid']} restarted successfully"))

            elif action == "config":
                response = service.get_container_config(node=options["node"], vmid=options["vmid"])
                self.stdout.write(json.dumps(response, indent=2))

            elif action == "exec":
                logger.debug("Starting exec command")
                logger.debug(f"Options: {options}")

                response = service.exec_command(
                    node=options["node"],
                    vmid=options["vmid"],
                    command=options["command"],
                    args=options.get("args", []),
                    poll=not options.get("no_poll", False),
                    poll_interval=options.get("poll_interval", 2),
                )

                logger.debug(f"Command response: {response}")

                if response.get("output"):
                    self.stdout.write(response["output"])
                if response.get("error"):
                    self.stderr.write(response["error"])

            elif action == "configure-network":
                service.configure_network(options["vmid"], options["net0"])
                self.stdout.write(
                    self.style.SUCCESS(f"Network configured for container {options['vmid']}: {options['net0']}")
                )

            else:
                raise CommandError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error occurred: {str(e)}", exc_info=True)
            raise CommandError(f"Failed to {action} container: {str(e)}")
