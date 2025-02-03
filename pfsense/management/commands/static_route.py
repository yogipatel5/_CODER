"""Management command for handling static routes."""

import json
import logging

from django.core.management.base import BaseCommand

from ...services.static_route import StaticRouteClient

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Manage pfSense static routes"

    def add_arguments(self, parser):
        parser.add_argument("action", choices=["list", "get", "create", "update", "delete"], help="Action to perform")
        parser.add_argument("--id", help="Route ID for get/update/delete actions")
        parser.add_argument("--data", type=str, help="JSON data for create/update actions")
        parser.add_argument("--limit", type=int, default=0, help="Number of routes to fetch (0 for no limit)")
        parser.add_argument("--offset", type=int, default=0, help="Starting point in the dataset")
        parser.add_argument("--sort-by", type=str, nargs="+", help="Fields to sort by")
        parser.add_argument("--sort-order", choices=["SORT_ASC", "SORT_DESC"], help="Sort order")

    def handle(self, *args, **options):
        client = StaticRouteClient()
        action = options["action"]

        try:
            if action == "list":
                response = client.get_static_routes(
                    limit=options["limit"],
                    offset=options["offset"],
                    sort_by=options["sort_by"],
                    sort_order=options["sort_order"],
                )
                self.stdout.write(json.dumps(response, indent=2))

            elif action == "get":
                if not options["id"]:
                    raise ValueError("ID is required for get action")
                response = client.get_static_route(options["id"])
                self.stdout.write(json.dumps(response, indent=2))

            elif action == "create":
                if not options["data"]:
                    raise ValueError("Data is required for create action")
                data = json.loads(options["data"])
                response = client.create_static_route(data)
                self.stdout.write(json.dumps(response, indent=2))
                if response.get("status") == "ok":
                    client.apply_changes()

            elif action == "update":
                if not options["id"] or not options["data"]:
                    raise ValueError("Both ID and data are required for update action")
                data = json.loads(options["data"])
                response = client.update_static_route(options["id"], data)
                self.stdout.write(json.dumps(response, indent=2))
                if response.get("status") == "ok":
                    client.apply_changes()

            elif action == "delete":
                if not options["id"]:
                    raise ValueError("ID is required for delete action")
                response = client.delete_static_route(options["id"])
                self.stdout.write(json.dumps(response, indent=2))
                if response.get("status") == "ok":
                    client.apply_changes()
                    self.stdout.write(self.style.SUCCESS(f"Route {options['id']} deleted successfully"))

        except Exception as e:
            logger.error(f"Error in static route command: {str(e)}")
            self.stdout.write(self.style.ERROR(str(e)))
