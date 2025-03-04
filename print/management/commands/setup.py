from django.core.management.base import BaseCommand
from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from print.models.task import Task


class Command(BaseCommand):
    help = "Setup initial configuration for print app"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Force setup even if already configured")

    def _setup_periodic_tasks(self):
        """Setup periodic tasks for the app."""
        self.stdout.write("Setting up periodic tasks...")

        # Create default interval schedules if they don't exist
        hourly, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.HOURS)
        daily, _ = IntervalSchedule.objects.get_or_create(every=1, period=IntervalSchedule.DAYS)

        # Define tasks to setup
        tasks_config = [
            {
                "name": "print_daily_task",
                "task": "print.tasks.daily_task",
                "schedule": daily,
                "description": "Daily maintenance task",
            },
            # Add more tasks as needed
        ]

        # Create tasks
        for config in tasks_config:
            task, created = Task.objects.get_or_create(
                name=config["name"],
                defaults={"description": config["description"], "last_run": timezone.now(), "is_enabled": True},
            )

            if created:
                # Create associated PeriodicTask
                periodic_task = PeriodicTask.objects.create(
                    name=config["name"], task=config["task"], interval=config["schedule"], start_time=timezone.now()
                )
                # Link PeriodicTask to our Task
                task.periodic_task = periodic_task
                task.save()

                self.stdout.write(self.style.SUCCESS(f"Created task: {config['name']}"))
            else:
                self.stdout.write(f"Task already exists: {config['name']}")

    def _setup_initial_data(self):
        """Setup any initial data required by the app."""
        self.stdout.write("Setting up initial data...")
        # Add your initial data setup here
        # Example:
        # MyModel.objects.get_or_create(name="default", defaults={...})

    def handle(self, *args, **options):
        force = options["force"]

        try:
            # Check if setup has already been run
            if not force and Task.objects.exists():
                self.stdout.write(self.style.WARNING("Setup has already been run. Use --force to run again."))
                return

            # Run setup steps
            self._setup_periodic_tasks()
            self._setup_initial_data()

            self.stdout.write(self.style.SUCCESS(f"Successfully setup {self.help}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during setup: {str(e)}"))
