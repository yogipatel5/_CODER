from django.core.management.base import BaseCommand

from notion.core.services import NotionService
from notion.tasks.scanning import scan_notion_for_notey_blocks


class Command(BaseCommand):
    help = "Scan Notion pages for blocks containing 'Notey' and create agent jobs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--celery",
            action="store_true",
            help="Run the task through Celery instead of directly",
        )

    def handle(self, *args, **options):
        if options["celery"]:
            # Schedule the task to run immediately through Celery
            task = scan_notion_for_notey_blocks.delay()
            self.stdout.write(self.style.SUCCESS(f"Successfully scheduled Notion scanning task (task id: {task.id})"))
        else:
            # Run the task directly
            service = NotionService()
            try:
                result = service.scan_for_notey_blocks()
                self.stdout.write(
                    self.style.SUCCESS(f"Successfully scanned Notion. Created {len(result)} new agent jobs.")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error scanning Notion: {str(e)}"))
