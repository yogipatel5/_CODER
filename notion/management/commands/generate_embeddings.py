import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from notion.models.page import Page
from notion.services.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate embeddings for all Notion pages"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=50,
            help="Number of pages to process in each batch (default: 50)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force regeneration of embeddings even if they already exist",
        )
        parser.add_argument(
            "--filter",
            type=str,
            help="Filter pages by title (case-insensitive contains)",
        )

    def handle(self, *args, **options):
        """Generate embeddings for all pages."""
        batch_size = options["batch_size"]
        force = options["force"]
        title_filter = options["filter"]

        # Get pages query
        pages = Page.objects.all()
        if not force:
            pages = pages.filter(embedding__isnull=True)
        if title_filter:
            pages = pages.filter(title__icontains=title_filter)

        total_pages = pages.count()
        if total_pages == 0:
            self.stdout.write("No pages found that need embeddings.")
            return

        self.stdout.write(f"\nGenerating embeddings for {total_pages} pages")
        self.stdout.write(f"Batch size: {batch_size}")
        if force:
            self.stdout.write("Force mode: ON - Regenerating all embeddings")
        if title_filter:
            self.stdout.write(f"Filtering pages by title: {title_filter}")
        self.stdout.write("")

        service = EmbeddingsService()
        success_count = 0
        error_count = 0
        error_pages = []

        # Process pages in batches with progress bar
        progress = tqdm(total=total_pages, desc="Processing pages")
        for i in range(0, total_pages, batch_size):
            batch = pages[i : i + batch_size]

            # Process each page in the batch
            for page in batch:
                try:
                    with transaction.atomic():
                        service.update_page_embeddings(page)
                        success_count += 1
                except Exception as e:
                    logger.error(f"Error processing page {page.id}: {str(e)}")
                    error_count += 1
                    error_pages.append((page.id, page.title, str(e)))
                finally:
                    progress.update(1)

        progress.close()

        # Print summary
        self.stdout.write("\nEmbedding Generation Summary:")
        self.stdout.write(f"Successfully processed: {success_count} pages")
        if error_count > 0:
            self.stdout.write(f"Errors encountered: {error_count} pages")
            self.stdout.write("\nPages with errors:")
            for page_id, title, error in error_pages:
                self.stdout.write(f"- {title} ({page_id}): {error}")

        self.stdout.write("\nDone!")
