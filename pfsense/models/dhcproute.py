from django.core.validators import validate_ipv4_address, validate_ipv6_address
from django.db import models


class DHCPRoute(models.Model):
    """Model for storing dynamic and static routes."""

    pfsense_id = models.CharField(max_length=100, help_text="ID of the route in pfSense")
    network = models.CharField(max_length=45, help_text="Network address (IPv4/IPv6)", unique=True)
    subnet = models.CharField(max_length=3, help_text="Subnet mask")
    gateway = models.CharField(
        max_length=45, validators=[validate_ipv4_address, validate_ipv6_address], help_text="Gateway IP address"
    )
    hostname = models.CharField(max_length=255, blank=True, help_text="Hostname for the route")
    description = models.CharField(max_length=255, blank=True, help_text="Route description")
    disabled = models.BooleanField(default=False, help_text="Route status")
    online_status = models.CharField(
        max_length=20,
        choices=[("active", "Active"), ("inactive", "Inactive")],
        blank=True,  # Maps both 'active' and 'online' to 'Active'
    )
    route_type = models.CharField(max_length=10, help_text="Type of the route (static or dynamic)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_synced = models.DateTimeField(auto_now=True, help_text="Last time this route was synced with pfSense")

    class Meta:
        db_table = "dhcp_routes"
        ordering = ["network", "subnet"]

    def __str__(self):
        hostname_str = f" ({self.hostname})" if self.hostname else ""
        return f"{self.network}/{self.subnet} via {self.gateway}{hostname_str}"

    def save(self, *args, **kwargs):
        # Convert 'online' or 'active/online' status to 'active'
        if self.online_status:
            if self.online_status.lower() in ["online", "active", "active/online"]:
                self.online_status = "active"
        super().save(*args, **kwargs)
