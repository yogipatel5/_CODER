import logging

from celery import shared_task
from django.utils import timezone

from pfsense.models.dhcproute import DHCPRoute
from pfsense.models.task import Tasks
from pfsense.services.dhcp_server import DHCPServerService

logger = logging.getLogger(__name__)


@shared_task
@Tasks.objects.create_task_wrapper("sync_dhcp_routes")
def sync_dhcp_routes():
    """Sync DHCP routes from pfSense to local database"""
    logger.info("Starting DHCP routes sync")
    service = DHCPServerService()
    routes = service.get_all()
    logger.info(f"Found {len(routes)} routes to sync")

    synced_count = 0
    for route in routes:
        # Determine if this is a static or dynamic route based on hostname
        # Static routes typically have a hostname set
        route_type = "dynamic" if route.active_status == "active" else "static"

        logger.info(f"Syncing {route_type} route: {route.ip} ({route.hostname or 'No hostname'})")
        DHCPRoute.objects.update_or_create(
            pfsense_id=str(route.id),
            defaults={
                "network": route.ip,
                "gateway": route.mac,  # MAC address is used as gateway in DHCP routes
                "description": route.descr or "",  # Use the description field from pfSense
                "hostname": route.hostname,  # Store hostname separately
                "disabled": route.active_status != "active",
                "route_type": route_type,
                "last_synced": timezone.now(),
            },
        )
        synced_count += 1

    logger.info(f"Successfully synced {synced_count} DHCP routes")
    return synced_count
