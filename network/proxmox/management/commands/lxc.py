"""Management command for LXC container operations."""

import logging

from django.core.management.base import BaseCommand, CommandError

from network.proxmox.services.lxc import LXCService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command for managing LXC containers in Proxmox."""

    help = "Manage LXC containers in Proxmox"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "action",
            choices=["list", "create", "status", "start", "stop", "shutdown", "delete", "logs"],
            help="Action to perform",
        )
        parser.add_argument("--node", default="pve", help="Proxmox node name (default: pve)")
        parser.add_argument("--vmid", type=int, help="Container ID (required for all actions except list)")

        # Create-specific arguments
        parser.add_argument("--ostemplate", help="OS template for container creation")
        parser.add_argument("--hostname", help="Hostname for new container")
        parser.add_argument("--storage", help="Storage location for new container")
        parser.add_argument("--password", help="Root password for new container")
        parser.add_argument("--memory", type=int, default=512, help="RAM in MB for new container")
        parser.add_argument("--cores", type=int, default=1, help="CPU cores for new container")

        # Shutdown-specific arguments
        parser.add_argument("--timeout", type=int, help="Shutdown timeout in seconds")

        # Delete-specific arguments
        parser.add_argument("--force", action="store_true", help="Force delete container even if running")

        # Logs-specific arguments
        parser.add_argument("--limit", type=int, default=500, help="Maximum number of log lines to show")

    def handle(self, *args, **options):
        """Handle the command."""
        service = LXCService()
        action = options["action"]
        node = options.get("node", "pve")
        vmid = options.get("vmid")

        try:
            if action == "list":
                containers = service.list_containers(node=node)
                self.stdout.write("Containers:")
                for container in containers:
                    self.stdout.write(
                        f"  - {container['vmid']}: {container.get('name', 'N/A')} "
                        f"(Status: {container.get('status', 'unknown')})"
                    )
                return

            if not vmid and action != "list":
                raise CommandError("--vmid is required for this action. Use 'list' to see available container IDs.")

            if action == "create":
                required = ["ostemplate", "hostname", "storage", "password"]
                missing = [arg for arg in required if not options.get(arg)]
                if missing:
                    raise CommandError(f"Missing required arguments for create: {', '.join(missing)}")

                result = service.create_container(
                    vmid=vmid,
                    ostemplate=options["ostemplate"],
                    hostname=options["hostname"],
                    storage=options["storage"],
                    password=options["password"],
                    node=node,
                    memory=options["memory"],
                    cores=options["cores"],
                )
                self.stdout.write(self.style.SUCCESS(f"Container creation initiated. Task: {result}"))

            elif action == "status":
                status = service.get_container_status(node=node, vmid=vmid)
                self.stdout.write("Container status:")
                for key, value in status.items():
                    self.stdout.write(f"  {key}: {value}")

            elif action == "start":
                result = service.start_container(node=node, vmid=vmid)
                self.stdout.write(self.style.SUCCESS(f"Container start initiated. Task: {result}"))

            elif action == "stop":
                result = service.stop_container(node=node, vmid=vmid)
                self.stdout.write(self.style.SUCCESS(f"Container stop initiated. Task: {result}"))

            elif action == "shutdown":
                if not vmid:
                    raise CommandError("--vmid is required for shutdown action")
                timeout = options.get("timeout")
                service.shutdown_container(node=node, vmid=vmid, timeout=timeout)
                self.stdout.write(f"Initiated shutdown for container {vmid}")

            elif action == "delete":
                if not vmid:
                    raise CommandError("--vmid is required for delete action")
                force = options.get("force", False)
                service.delete_container(node=node, vmid=vmid, force=force)
                self.stdout.write(f"Deleted container {vmid}")

            elif action == "logs":
                if not vmid:
                    raise CommandError("--vmid is required for logs action")
                limit = options.get("limit", 500)
                logs = service.get_container_logs(node=node, vmid=vmid, limit=limit)
                self.stdout.write(f"Logs for container {vmid}:")
                for log in logs:
                    self.stdout.write(f"  {log}")

        except Exception as e:
            raise CommandError(f"Failed to {action} container: {str(e)}")
