"""Admin interface for DHCP routes."""

from django.contrib import admin

from pfsense.models.dhcproute import DHCPRoute


@admin.register(DHCPRoute)
class DHCPRouteAdmin(admin.ModelAdmin):
    list_display = [
        "network",
        "subnet",
        "gateway",
        "description",
        "disabled",
        "route_type",
        "online_status",
        "last_synced",
    ]
    list_filter = ["disabled", "route_type"]
    search_fields = ["network", "gateway", "description", "pfsense_id"]
    readonly_fields = ["pfsense_id", "created_at", "updated_at", "last_synced"]
    ordering = ["network", "subnet"]
