from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from notifier.services.notify_me import PRIORITY_HIGH, NotifyMeTask
from pfsense.models.dhcproute import DHCPRoute
from pfsense.models.task import Task
from pfsense.services.dhcp_server import DHCPServerService

logger = get_task_logger(__name__)


def notify_error(task_name, error_message):
    """Send error notification using NotifyMeTask"""
    title = f"pfSense Task Error: {task_name}"
    NotifyMeTask.notify_me(
        message=error_message,
        title=title,
        priority=PRIORITY_HIGH,
    )


# Apply decorators in the correct order:
# 1. create_task_wrapper first (inner)
# 2. shared_task second (outer)
# @Task.objects.create_task_wrapper("pfsense.tasks.sync_dhcp_routes")
@shared_task(name="pfsense.tasks.sync_dhcp_routes")
def sync_dhcp_routes():
    """Sync DHCP routes from pfSense to local database."""
    logger.info("Starting DHCP routes sync")

    service = DHCPServerService()

    # Get routes from pfSense
    pfsense_routes = service.get_all()
    logger.debug(f"Raw response: {pfsense_routes}")
    if not pfsense_routes:
        logger.warning("No routes returned from pfSense")
        return {"message": "No routes returned from pfSense", "count": 0}

    # Update local database
    for route in pfsense_routes:
        try:
            # Get a valid gateway - either the interface IP or a default
            gateway = route.ip  # Use the IP as gateway since we don't have a better option

            DHCPRoute.objects.update_or_create(
                pfsense_id=str(route.id),  # Use the pfSense ID as unique identifier
                defaults={
                    "network": route.ip,  # Using IP as network
                    "gateway": gateway,  # Using IP as gateway since we need a valid IP
                    "subnet": getattr(route, "subnet", "24"),  # Default to /24 if not provided
                    "hostname": route.hostname or "",  # Empty string if None
                    "description": route.descr or "",  # Empty string if None
                    "route_type": "dynamic",
                    "last_synced": timezone.now(),
                },
            )
        except (AttributeError, KeyError) as e:
            logger.error(f"Error processing route {route}: {str(e)}")
            raise  # Re-raise to let the wrapper handle it

    count = len(pfsense_routes)
    logger.info(f"Successfully synced {count} routes")
    return {"message": f"Synced {count} routes", "count": count}
