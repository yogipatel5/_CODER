import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from ..api.client import PFSenseClient
from ..api.exceptions import PFSenseAPIException

logger = logging.getLogger(__name__)


@dataclass
class StaticMap:
    parent_id: str
    id: int
    mac: str
    ipaddr: str
    cid: str = ""
    hostname: str = ""
    domain: str = ""
    domainsearchlist: List[str] = None
    defaultleasetime: Optional[int] = None
    maxleasetime: Optional[int] = None
    gateway: str = ""
    dnsserver: Optional[List[str]] = None
    winsserver: Optional[List[str]] = None
    ntpserver: Optional[List[str]] = None
    arp_table_static_entry: bool = False
    descr: str = ""

    def to_dict(self) -> Dict:
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class DHCPServer:
    id: int
    ip: str
    mac: str
    hostname: str
    if_name: str = ""  # Renamed from 'if'
    starts: str = ""
    ends: str = ""
    active_status: str = ""
    online_status: str = ""
    descr: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary, mapping if_name back to 'if'"""
        data = {k: v for k, v in self.__dict__.items() if v is not None}
        if "if_name" in data:
            data["if"] = data.pop("if_name")
        return data


class DHCPServerService:
    def __init__(self, client: PFSenseClient = None):
        self.client = client or PFSenseClient()

    def get_all(self, mac: str = None, ip: str = None, hostname: str = None) -> List[DHCPServer]:
        """Get all DHCP leases with optional filtering"""
        try:
            response = self.client.get("status/dhcp_server/leases")

            servers = []
            for server_data in response.get("data", []):
                # Skip if filters don't match
                if mac and server_data.get("mac", "").lower() != mac.lower():
                    continue
                if ip and server_data.get("ip") != ip:
                    continue
                if hostname and server_data.get("hostname", "").lower() != hostname.lower():
                    continue

                # Rename 'if' to 'if_name' before creating DHCPServer object
                if "if" in server_data:
                    server_data["if_name"] = server_data.pop("if")

                servers.append(DHCPServer(**server_data))
            return servers
        except PFSenseAPIException as e:
            logger.error(f"Failed to get DHCP servers: {str(e)}")
            raise

    def get(self, server_id: str) -> DHCPServer:
        """Get a specific DHCP server"""
        try:
            response = self.client.get(f"services/dhcp_server/{server_id}")
            server_data = response.get("data", {})
            staticmaps = [StaticMap(**sm) for sm in server_data.get("staticmap", [])]
            server_data["staticmap"] = staticmaps
            return DHCPServer(**server_data)
        except PFSenseAPIException as e:
            logger.error(f"Failed to get DHCP server {server_id}: {str(e)}")
            raise

    def create(self, server: DHCPServer) -> DHCPServer:
        """Create a new DHCP server"""
        try:
            response = self.client.post("services/dhcp_server", json=server.to_dict())
            return DHCPServer(**response.get("data", {}))
        except PFSenseAPIException as e:
            logger.error(f"Failed to create DHCP server: {str(e)}")
            raise

    def update(self, server: DHCPServer) -> DHCPServer:
        """Update an existing DHCP server"""
        try:
            response = self.client.put(f"services/dhcp_server/{server.id}", json=server.to_dict())
            return DHCPServer(**response.get("data", {}))
        except PFSenseAPIException as e:
            logger.error(f"Failed to update DHCP server {server.id}: {str(e)}")
            raise

    def delete(self, server_id: str) -> bool:
        """Delete a DHCP server"""
        try:
            self.client.delete(f"services/dhcp_server/{server_id}")
            return True
        except PFSenseAPIException as e:
            logger.error(f"Failed to delete DHCP server {server_id}: {str(e)}")
            raise

    def add_static_map(self, server_id: str, static_map: StaticMap) -> DHCPServer:
        """Add a static map to a DHCP server"""
        try:
            response = self.client.post(f"services/dhcp_servers/{server_id}/staticmap", json=static_map.to_dict())
            return DHCPServer(**response.get("data", {}))
        except PFSenseAPIException as e:
            logger.error(f"Failed to add static map to server {server_id}: {str(e)}")
            raise

    def remove_static_map(self, server_id: str, static_map_id: int) -> bool:
        """Remove a static map from a DHCP server"""
        try:
            self.client.delete(f"services/dhcp_servers/{server_id}/staticmap/{static_map_id}")
            return True
        except PFSenseAPIException as e:
            logger.error(f"Failed to remove static map {static_map_id} from server {server_id}: {str(e)}")
            raise
