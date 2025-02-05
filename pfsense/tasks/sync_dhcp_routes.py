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


@shared_task(name="pfsense.tasks.sync_dhcp_routes")
def sync_dhcp_routes():
    """Sync DHCP routes from pfSense to local database.

    Returns:
        int: Number of routes synced, or None if error
    """
    logger.info("Starting DHCP routes sync")
    try:
        # Get task configuration
        task = Task.objects.get(name="sync_dhcp_routes")
        if not task.is_active:
            logger.warning("Task is not active, skipping execution")
            return None

        service = DHCPServerService()

        # Get routes from pfSense
        pfsense_routes = service.get_all()
        logger.debug(f"Raw response: {pfsense_routes}")
        if not pfsense_routes:
            logger.warning("No routes returned from pfSense")
            return None

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

        count = len(pfsense_routes)
        logger.info(f"Successfully synced {count} routes")

        # Update task status
        task.last_status = "success"
        task.last_result = {"count": count}
        task.last_run = timezone.now()
        task.save()

        # Update error statuses using manager
        task.errors.update_regressed_errors(task)

        return count

    except Exception as e:
        error_msg = f"Failed to sync DHCP routes: {str(e)}"
        logger.error(error_msg)

        try:
            task = Task.objects.get(name="sync_dhcp_routes")
            task.last_status = "error"
            task.last_error = error_msg
            task.last_run = timezone.now()

            # Log error using manager
            import sys

            task.errors.log_error(task, e, sys.exc_info()[2])

            if task.notify_on_error:
                notify_error("sync_dhcp_routes", error_msg)

            if task.disable_on_error:
                task.is_active = False
                logger.info("Task disabled due to error")

            task.save()
        except Exception as inner_e:
            logger.error(f"Failed to update task status: {str(inner_e)}")

        return None
