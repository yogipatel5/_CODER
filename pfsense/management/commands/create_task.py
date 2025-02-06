from django.utils import timezone
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from pfsense.management.commands._base import pfsense_HelperCommand
from pfsense.models.task import Task


class Command(pfsense_HelperCommand):
    help = "Create a new periodic task along with a app task with Celery Beat integration"

    def add_arguments(self, parser):
        parser.add_argument("name", type=str, help="Name of the task")
        parser.add_argument("task_path", type=str, help="Full path to the task function (e.g., app_name.tasks.my_task)")
        parser.add_argument("--description", type=str, help="Description of what the task does")
        parser.add_argument(
            "--schedule-type",
            type=str,
            choices=["minutes", "hours", "days"],
            default="hours",
            help="Schedule interval type",
        )
        parser.add_argument("--schedule-every", type=int, default=1, help="Run task every X schedule-type (default: 1)")
        parser.add_argument("--notify-on-error", action="store_true", help="Send notifications on errors")
        parser.add_argument("--disable-on-error", action="store_true", help="Disable task on errors")
        parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retry attempts")

    def handle(self, *args, **options):
        name = options["name"]
        task_path = options["task_path"]

        # Create interval schedule
        schedule_type = options["schedule_type"].upper()
        schedule_every = options["schedule_every"]

        schedule, _ = IntervalSchedule.objects.get_or_create(
            every=schedule_every,
            period=getattr(IntervalSchedule, schedule_type),
        )

        # Create or update the Celery periodic task
        periodic_task, _ = PeriodicTask.objects.get_or_create(
            name=name,  # Use the same name for both Task and PeriodicTask
            defaults={
                "task": task_path,
                "interval": schedule,
                "enabled": True,
                "one_off": False,
                "start_time": timezone.now(),
            },
        )

        # Create or update the task
        task, created = Task.objects.get_or_create(
            name=name,
            defaults={
                "description": options.get("description", ""),
                "is_active": True,
                "notify_on_error": options["notify_on_error"],
                "disable_on_error": options["disable_on_error"],
                "max_retries": options["max_retries"],
                "schedule": f"Every {schedule_every} {schedule_type.lower()}",
                "periodic_task": periodic_task,
            },
        )

        # Update existing task if needed
        if not created:
            task.description = options.get("description", task.description)
            task.notify_on_error = options["notify_on_error"]
            task.disable_on_error = options["disable_on_error"]
            task.max_retries = options["max_retries"]
            task.schedule = f"Every {schedule_every} {schedule_type.lower()}"
            task.periodic_task = periodic_task
            task.save()

        if created:
            self.log_success(f"Created new task '{name}' with periodic schedule")
        else:
            self.log_success(f"Updated existing task '{name}' with new settings")
