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


@shared_task
@Task.objects.create_task_wrapper("sync_dhcp_routes")
def sync_dhcp_routes():
    """Sync DHCP routes from pfSense to local database.

    Returns:
        int: Number of routes synced, or None if error
    """
    logger.info("Starting DHCP routes sync")
    try:
        service = DHCPServerService()

        # Get routes from pfSense
        pfsense_routes = service.get_dhcp_routes()
        if not pfsense_routes:
            logger.warning("No routes returned from pfSense")
            return None

        # Update local database
        for route in pfsense_routes:
            DHCPRoute.objects.update_or_create(
                network=route["network"],
                defaults={
                    "gateway": route["gateway"],
                    "subnet": route["subnet"],
                    "last_sync": timezone.now(),
                },
            )

        count = len(pfsense_routes)
        logger.info(f"Successfully synced {count} routes")
        return count

    except Exception as e:
        error_msg = f"Failed to sync DHCP routes: {str(e)}"
        logger.error(error_msg)

        try:
            task = Task.objects.get(name="sync_dhcp_routes")
            task.last_status = "error"
            task.last_error = error_msg
            task.last_run = timezone.now()

            if task.notify_on_error:
                notify_error("sync_dhcp_routes", error_msg)

            if task.disable_on_error:
                task.is_active = False
                logger.info("Task disabled due to error")

            task.save()
        except Exception as inner_e:
            logger.error(f"Failed to update task status: {str(inner_e)}")

        return None
