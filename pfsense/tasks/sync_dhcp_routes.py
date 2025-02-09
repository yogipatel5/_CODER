from celery.utils.log import get_task_logger
from django.utils import timezone

from pfsense.models.dhcproute import DHCPRoute
from pfsense.services.dhcp_server import DHCPServerService
from shared.celery.task import shared_task  # Use our enhanced shared_task

logger = get_task_logger(__name__)


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

    updates = 0
    creates = 0
    deletes = 0

    # Create a set of valid pfsense_ids from the API response
    valid_pfsense_ids = {str(route.id) for route in pfsense_routes}

    # Delete any routes that no longer exist in pfSense
    deleted = DHCPRoute.objects.exclude(pfsense_id__in=valid_pfsense_ids).delete()
    deletes = deleted[0] if deleted else 0
    logger.info(f"Deleted {deletes} routes that no longer exist in pfSense")

    # Update local database
    for route in pfsense_routes:
        try:
            # Get a valid gateway - either the interface IP or a default
            gateway = route.ip  # Use the IP as gateway since we don't have a better option
            pfsense_id = str(route.id)

            route_data = {
                "network": route.ip,  # Using IP as network
                "gateway": gateway,  # Using IP as gateway since we need a valid IP
                "subnet": getattr(route, "subnet", "24"),  # Default to /24 if not provided
                "hostname": route.hostname or "",  # Empty string if None
                "description": route.descr or "",  # Empty string if None
                "route_type": route.active_status,
                "online_status": route.online_status,
                "last_synced": timezone.now(),
            }

            logger.info(f"Processing route: pfsense_id={pfsense_id}, network={route_data['network']}")

            # First, try to find route by pfsense_id
            existing_route = DHCPRoute.objects.filter(pfsense_id=pfsense_id).first()

            # If we're going to update a network, check if another route has it
            if existing_route and _routes_are_different(existing_route, route_data):
                # Find any routes with the target network (excluding current route)
                conflicting_routes = DHCPRoute.objects.filter(network=route_data["network"]).exclude(
                    pfsense_id=pfsense_id
                )

                # If there are conflicts, delete them as they're outdated
                if conflicting_routes.exists():
                    logger.warning(
                        f"Found conflicting routes for network {route_data['network']}, "
                        f"pfsense_ids: {[r.pfsense_id for r in conflicting_routes]}. "
                        f"These will be deleted as they are outdated."
                    )
                    deleted = conflicting_routes.delete()
                    deletes += deleted[0]

                # Now safe to update
                logger.info(
                    f"Updating route: pfsense_id={pfsense_id}\n"
                    f"Old values: network={existing_route.network}, gateway={existing_route.gateway}\n"
                    f"New values: network={route_data['network']}, gateway={route_data['gateway']}"
                )

                for key, value in route_data.items():
                    setattr(existing_route, key, value)
                existing_route.save()
                updates += 1
                logger.info(f"Successfully updated route: pfsense_id={pfsense_id}")

            elif not existing_route:
                # Handle any conflicting routes before creating
                conflicting_routes = DHCPRoute.objects.filter(network=route_data["network"])
                if conflicting_routes.exists():
                    logger.warning(
                        f"Found conflicting routes for network {route_data['network']}, "
                        f"pfsense_ids: {[r.pfsense_id for r in conflicting_routes]}. "
                        f"These will be deleted as they are outdated."
                    )
                    deleted = conflicting_routes.delete()
                    deletes += deleted[0]

                # Now safe to create
                DHCPRoute.objects.create(pfsense_id=pfsense_id, **route_data)
                creates += 1
                logger.info(f"Created new route: pfsense_id={pfsense_id}")

        except (AttributeError, KeyError) as e:
            logger.error(f"Error processing route {route}: {str(e)}")
            raise  # Re-raise to let the wrapper handle it

    logger.info(f"Successfully synced routes: {creates} created, {updates} updated, {deletes} deleted")
    return f"Synced routes: {creates} created, {updates} updated, {deletes} deleted"
