from django.core.management.base import BaseCommand

from notion.services.sync import NotionSyncService
from notion.tasks.sync import sync_notion_content


class Command(BaseCommand):
    """Sync all Notion content (pages and databases)."""

    help = "Sync all Notion content (pages and databases)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--celery",
            action="store_true",
            help="Run the sync task through Celery instead of directly",
        )

    def handle(self, *args, **options):
        if options["celery"]:
            # Schedule the task to run immediately through Celery
            task = sync_notion_content.delay()
            self.stdout.write(self.style.SUCCESS(f"Successfully scheduled Notion sync task (task id: {task.id})"))
        else:
            # Run the sync directly
            service = NotionSyncService()
            try:
                result = service.sync_all()
                self.stdout.write(self.style.SUCCESS(f"Successfully synced Notion content: {result}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error syncing Notion content: {str(e)}"))
