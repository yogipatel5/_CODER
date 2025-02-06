"""Setup command for pfsense app."""

import logging
from typing import Any, Dict

from django.core.management.base import BaseCommand
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from pfsense.models.task import Task
from pfsense.tasks.sync_dhcp_routes import sync_dhcp_routes

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Setup initial configuration for pfsense app."""

    help = "Setup initial configuration for pfsense app"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force setup even if already configured",
        )
        parser.add_argument(
            "--skip-sync",
            action="store_true",
            help="Skip initial DHCP routes sync",
        )

    def _setup_periodic_tasks(self):
        """Setup periodic tasks for the app."""
        self.stdout.write("Setting up periodic tasks...")

        try:
            # Create default interval schedules
            schedules = {
                "hourly": IntervalSchedule.objects.get_or_create(
                    every=1,
                    period=IntervalSchedule.HOURS,
                )[0],
                "daily": IntervalSchedule.objects.get_or_create(
                    every=1,
                    period=IntervalSchedule.DAYS,
                )[0],
            }

            # Define tasks configuration
            tasks_config = [
                {
                    "name": "sync_dhcp_routes",
                    "description": "Sync DHCP routes from pfSense to local database",
                    "task": "pfsense.tasks.sync_dhcp_routes",
                    "schedule": schedules["hourly"],
                    "notify_on_error": True,
                    "disable_on_error": False,
                    "max_retries": 3,
                },
            ]

            # Setup each task
            for config in tasks_config:
                # First create/update the periodic task
                periodic_task = PeriodicTask.objects.update_or_create(
                    name=config["name"],
                    defaults={
                        "task": config["task"],
                        "interval": config["schedule"],
                        "enabled": True,
                        "one_off": False,
                        "start_time": timezone.now(),
                    },
                )[0]

                # Then create/update our task without select_for_update
                task = Task.objects.filter(name=config["name"]).first()
                if task:
                    # Update existing task
                    task.description = config["description"]
                    task.notify_on_error = config.get("notify_on_error", True)
                    task.disable_on_error = config.get("disable_on_error", False)
                    task.max_retries = config.get("max_retries", 3)
                    task.schedule = f"Every {config['schedule'].every} {config['schedule'].period}"
                    task.periodic_task = periodic_task
                    task.is_active = True
                    task.save()
                else:
                    # Create new task
                    task = Task.objects.create(
                        name=config["name"],
                        description=config["description"],
                        notify_on_error=config.get("notify_on_error", True),
                        disable_on_error=config.get("disable_on_error", False),
                        max_retries=config.get("max_retries", 3),
                        schedule=f"Every {config['schedule'].every} {config['schedule'].period}",
                        periodic_task=periodic_task,
                        is_active=True,
                    )

                self.stdout.write(self.style.SUCCESS(f"Created/updated task: {config['name']}"))

            self.stdout.write(self.style.SUCCESS("Successfully setup periodic tasks"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to setup periodic tasks: {str(e)}"))
            raise

    def handle(self, *args, **options):
        """Handle command execution."""
        force = options["force"]
        skip_sync = options["skip_sync"]

        # Check if already configured
        if Task.objects.exists() and not force:
            self.stdout.write("App is already configured. Use --force to reconfigure.")
            return

        # Setup periodic tasks
        self._setup_periodic_tasks()

        # Run initial sync if requested
        if not skip_sync:
            self.stdout.write("Running initial DHCP routes sync...")
            try:
                result = sync_dhcp_routes()
                if result:
                    self.stdout.write(self.style.SUCCESS(f"Successfully synced {result} routes"))
                else:
                    self.stdout.write(self.style.WARNING("No routes synced"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to run initial sync: {str(e)}"))

        self.stdout.write(self.style.SUCCESS("Successfully setup pfsense app"))
