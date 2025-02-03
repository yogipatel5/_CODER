# /pfsense/management/commands/dhcp_server.py
import json

from django.core.management.base import BaseCommand, CommandError

from pfsense.services.dhcp_server import DHCPServerService


class Command(BaseCommand):
    help = "Manage DHCP servers"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["list", "get"])
        parser.add_argument("--mac", help="Filter by MAC address")
        parser.add_argument("--ip", help="Filter by IP address")
        parser.add_argument("--hostname", help="Filter by hostname")
        parser.add_argument("--table", action="store_true", help="Output in table format")

    def handle(self, *args, **options):
        service = DHCPServerService()
        action = options["action"]

        try:
            if action == "list":
                servers = service.get_all(
                    mac=options.get("mac"), ip=options.get("ip"), hostname=options.get("hostname")
                )
                self._output_servers(servers, table_format=options.get("table", False))

        except Exception as e:
            raise CommandError(str(e))

    def _output_servers(self, servers, table_format=False):
        if not table_format:
            data = [server.to_dict() for server in servers]
            self.stdout.write(json.dumps(data, indent=2))
        else:
            # Table format
            self.stdout.write(f"{'ID':<5} {'IP':<15} {'MAC':<18} {'Hostname':<20} {'Interface':<10} {'Status':<15}")
            self.stdout.write("-" * 85)
            for server in servers:
                # Convert None values to empty strings
                id_str = str(server.id) if server.id is not None else ""
                ip_str = server.ip or ""
                mac_str = server.mac or ""
                hostname_str = server.hostname or ""
                if_str = server.if_name or ""
                status_str = server.active_status or ""

                self.stdout.write(
                    f"{id_str:<5} {ip_str:<15} {mac_str:<18} {hostname_str:<20} " f"{if_str:<10} {status_str:<15}"
                )
