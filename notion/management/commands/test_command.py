import logging

from django.core.management.base import BaseCommand

from notion.models.page import Page

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Test command to retrieve and display a page's content"

    def add_arguments(self, parser):
        parser.add_argument("page_id", type=str, help="ID of the page to retrieve")

    def handle(self, *args, **options):
        page_id = options["page_id"]
        self.stdout.write(f"Attempting to retrieve page with ID: {page_id}")

        try:
            # Get the page markdown using the manager
            markdown_content = Page.objects.get_page_markdown(page_id)

            self.stdout.write("\nPage content in Markdown:")
            self.stdout.write("------------------------")
            self.stdout.write(markdown_content)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error retrieving page: {str(e)}"))
