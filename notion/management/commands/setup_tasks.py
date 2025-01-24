"""Management command to set up periodic Celery tasks."""

from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask

from notion.models import Task


class Command(BaseCommand):
    """Set up periodic tasks for the application."""

    help = "Set up periodic Celery tasks"

    def handle(self, *args, **kwargs):
        """Create the periodic tasks."""
        # Create or get schedules
        one_minute_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        five_minute_schedule, _ = IntervalSchedule.objects.get_or_create(
            every=5,
            period=IntervalSchedule.MINUTES,
        )

        # Create or update tasks in our Task model
        scan_task, _ = Task.objects.get_or_create(
            name="scan_notion_for_notey_blocks",
            defaults={
                "description": "Scans Notion pages for blocks containing 'Notey' and creates agent jobs",
                "is_active": True,
                "notify_on_error": True,
                "disable_on_error": False,
                "max_retries": 3,
                "schedule": "*/1 * * * *",  # Every minute in cron format
                "config": {"last_checked_time": None},
            },
        )

        process_task, _ = Task.objects.get_or_create(
            name="process_pending_jobs",
            defaults={
                "description": "Process pending Notion agent jobs",
                "is_active": True,
                "notify_on_error": True,
                "disable_on_error": False,
                "max_retries": 3,
                "schedule": "*/5 * * * *",  # Every 5 minutes in cron format
            },
        )

        # Create or update the Celery periodic tasks
        PeriodicTask.objects.get_or_create(
            name="Scan Notion for Notey blocks",
            task="notion.tasks.scanning.scan_notion_for_notey_blocks",
            interval=one_minute_schedule,
            defaults={
                "enabled": scan_task.is_active,
            },
        )

        PeriodicTask.objects.get_or_create(
            name="Process Pending Notion Jobs",
            task="notion.tasks.processing.process_pending_jobs",
            interval=five_minute_schedule,
            defaults={
                "enabled": process_task.is_active,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully set up periodic tasks:\n"
                f"- Scan task: {'enabled' if scan_task.is_active else 'disabled'}\n"
                f"- Process task: {'enabled' if process_task.is_active else 'disabled'}"
            )
        )
