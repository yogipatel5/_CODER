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

    def _setup_task(self, config: Dict[str, Any]) -> Task:
        """Setup a single task with its periodic schedule.

        Args:
            config: Task configuration dictionary

        Returns:
            Task: The created or updated task
        """
        # Get or create the task
        task, created = Task.objects.get_or_create(
            name=config["name"],
            defaults={
                "description": config["description"],
                "notify_on_error": config.get("notify_on_error", True),
                "disable_on_error": config.get("disable_on_error", False),
                "max_retries": config.get("max_retries", 3),
            },
        )

        # Update task fields if not created
        if not created:
            task.description = config["description"]
            task.notify_on_error = config.get("notify_on_error", True)
            task.disable_on_error = config.get("disable_on_error", False)
            task.max_retries = config.get("max_retries", 3)

        # Create or update the periodic task
        periodic_task, _ = PeriodicTask.objects.update_or_create(
            name=config["name"],
            defaults={
                "task": config["task"],
                "interval": config["schedule"],
                "enabled": True,
                "one_off": False,
                "start_time": timezone.now(),
            },
        )

        # Link periodic task and update schedule description
        task.periodic_task = periodic_task
        task.schedule = f"Every {config['schedule'].every} {config['schedule'].period}"
        task.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} task: {config['name']}"))
        return task

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
                    "task": "pfsense.tasks.sync_dhcp_routes.sync_dhcp_routes",
                    "schedule": schedules["hourly"],
                    "description": "Sync DHCP routes from pfSense to local database",
                    "notify_on_error": True,
                    "disable_on_error": False,
                    "max_retries": 3,
                },
                # Add more tasks here as needed
            ]

            # Setup each task
            for config in tasks_config:
                self._setup_task(config)

        except Exception as e:
            logger.error("Failed to setup periodic tasks: %s", str(e))
            raise

    def _perform_initial_sync(self):
        """Perform initial DHCP routes sync."""
        self.stdout.write("Starting initial DHCP routes sync...")
        try:
            task = Task.objects.get(name="sync_dhcp_routes")
            count = sync_dhcp_routes()

            if count is None:
                task.last_status = "error"
                task.last_error = "No routes were synced. Check the logs for details."
                self.stdout.write(self.style.WARNING(task.last_error))
            else:
                task.last_status = "success"
                task.last_result = {"synced_routes": count}
                self.stdout.write(self.style.SUCCESS(f"Successfully synced {count} DHCP routes"))

            task.last_run = timezone.now()
            task.save()

        except Exception as e:
            logger.error("Initial sync failed: %s", str(e))
            self.stdout.write(self.style.ERROR(f"Initial sync failed: {str(e)}"))
            raise

    def handle(self, *args, **options):
        """Handle the command execution."""
        force = options["force"]
        skip_sync = options["skip_sync"]

        try:
            # Check if setup has already been run
            if not force and Task.objects.exists():
                self.stdout.write(self.style.WARNING("Setup has already been run. Use --force to run again."))
                return

            self._setup_periodic_tasks()

            if not skip_sync:
                self._perform_initial_sync()

            self.stdout.write(self.style.SUCCESS("Setup completed successfully"))

        except Exception as e:
            logger.error("Setup failed: %s", str(e))
            self.stdout.write(self.style.ERROR(f"Setup failed: {str(e)}"))
            raise
