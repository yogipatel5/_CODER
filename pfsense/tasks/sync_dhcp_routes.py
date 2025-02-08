from celery.utils.log import get_task_logger
from django.utils import timezone

from notifier.services.notify_me import PRIORITY_HIGH, NotifyMeTask
from pfsense.models.dhcproute import DHCPRoute
from pfsense.services.dhcp_server import DHCPServerService
from shared.celery.task import shared_task  # Use our enhanced shared_task

logger = get_task_logger(__name__)


def notify_error(task_name, error_message):
    """Send error notification using NotifyMeTask"""
    title = f"pfSense Task Error: {task_name}"
    NotifyMeTask.notify_me(
        message=error_message,
        title=title,
        priority=PRIORITY_HIGH,
    )


def _routes_are_different(existing_route, new_data):
    """Compare existing route with new data to determine if update is needed."""
    return (
        existing_route.network != new_data["network"]
        or existing_route.gateway != new_data["gateway"]
        or existing_route.subnet != new_data["subnet"]
        or existing_route.hostname != new_data["hostname"]
        or existing_route.description != new_data["description"]
        or existing_route.route_type != new_data["route_type"]
    )


@shared_task(
    bind=False,
    schedule={
        "type": "interval",
        "every": 1,
        "period": "hours",  # Use lowercase for timedelta
    },
    description="Sync DHCP routes from pfSense to local database",
    notify_on_error=True,
    disable_on_error=False,
    max_retries=3,
)
def sync_dhcp_routes():
    """Sync DHCP routes from pfSense to local database."""
    logger.info("Starting DHCP routes sync")

    service = DHCPServerService()

    # Get routes from pfSense
    pfsense_routes = service.get_all()
    logger.debug(f"Raw response: {pfsense_routes}")
    if not pfsense_routes:
        logger.warning("No routes returned from pfSense")
        return "No routes returned from pfSense"

    # Prefetch all existing routes
    existing_routes = {str(route.pfsense_id): route for route in DHCPRoute.objects.all()}

    updates = 0
    creates = 0

    # Update local database
    for route in pfsense_routes:
        try:
            # Get a valid gateway - either the interface IP or a default
            gateway = route.ip  # Use the IP as gateway since we don't have a better option

            route_data = {
                "network": route.ip,  # Using IP as network
                "gateway": gateway,  # Using IP as gateway since we need a valid IP
                "subnet": getattr(route, "subnet", "24"),  # Default to /24 if not provided
                "hostname": route.hostname or "",  # Empty string if None
                "description": route.descr or "",  # Empty string if None
                "route_type": "dynamic",
                "last_synced": timezone.now(),
            }

            pfsense_id = str(route.id)
            existing_route = existing_routes.get(pfsense_id)

            if existing_route:
                if _routes_are_different(existing_route, route_data):
                    for key, value in route_data.items():
                        setattr(existing_route, key, value)
                    existing_route.save()
                    updates += 1
            else:
                DHCPRoute.objects.create(pfsense_id=pfsense_id, **route_data)
                creates += 1

        except (AttributeError, KeyError) as e:
            logger.error(f"Error processing route {route}: {str(e)}")
            raise  # Re-raise to let the wrapper handle it

    logger.info(f"Successfully synced routes: {creates} created, {updates} updated")
    return f"Synced routes: {creates} created, {updates} updated"
