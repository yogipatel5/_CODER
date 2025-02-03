from django.core.management.base import BaseCommand

from ...models.task import Tasks
from ...tasks.sync_dhcp_routes import sync_dhcp_routes


class Command(BaseCommand):
    help = "Initial sync of DHCP routes from pfSense"

    def handle(self, *args, **options):
        # Ensure task configuration exists
        Tasks.objects.get_or_create(
            name="sync_dhcp_routes",
            defaults={
                "description": "Sync DHCP routes from pfSense to local database",
                "is_active": True,
                "notify_on_error": True,
                "disable_on_error": False,
                "max_retries": 3,
            },
        )

        self.stdout.write("Starting initial DHCP routes sync...")
        count = sync_dhcp_routes()
        if count is None:
            self.stdout.write(self.style.WARNING("No routes were synced. Check the logs for details."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully synced {count} DHCP routes"))
