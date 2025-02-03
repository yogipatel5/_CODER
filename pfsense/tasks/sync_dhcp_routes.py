from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone

from notifier.services.notify_me import PRIORITY_HIGH, NotifyMeTask
from pfsense.models.dhcproute import DHCPRoute
from pfsense.models.task import Tasks
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
@Tasks.objects.create_task_wrapper("sync_dhcp_routes")
def sync_dhcp_routes():
    """Sync DHCP routes from pfSense to local database"""
    task = Tasks.objects.get(name="sync_dhcp_routes")

    try:
        logger.info("Starting DHCP routes sync")
        service = DHCPServerService()
        routes = service.get_all()
        logger.info(f"Found {len(routes)} routes to sync")

        synced_count = 0
        for route in routes:
            try:
                route_type = "dynamic" if route.active_status == "active" else "static"
                logger.info(f"Syncing {route_type} route: {route.ip} ({route.hostname or 'No hostname'})")

                DHCPRoute.objects.update_or_create(
                    pfsense_id=str(route.id),
                    defaults={
                        "network": route.ip,
                        "gateway": route.mac,
                        "description": route.descr or "",
                        "hostname": route.hostname,
                        "disabled": route.active_status != "active",
                        "route_type": route_type,
                        "last_synced": timezone.now(),
                    },
                )
                synced_count += 1
            except Exception as e:
                error_msg = f"Error syncing route {route.ip}: {str(e)}"
                logger.error(error_msg)
                if task.notify_on_error:
                    notify_error("sync_dhcp_routes", error_msg)
                continue

        logger.info(f"Successfully synced {synced_count} DHCP routes")
        task.last_run = timezone.now()
        task.save()
        return synced_count

    except Exception as e:
        error_msg = f"DHCP route sync failed: {str(e)}"
        logger.error(error_msg)

        if task.notify_on_error:
            notify_error("sync_dhcp_routes", error_msg)

        if task.disable_on_error:
            task.is_active = False
            task.save()
            logger.info("Task disabled due to error")

        raise  # Re-raise the exception for Celery to handle retries
