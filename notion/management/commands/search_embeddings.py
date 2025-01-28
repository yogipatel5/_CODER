import logging

from django.core.management.base import BaseCommand

from notion.services.embeddings import EmbeddingsService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Search for similar pages using embeddings"

    def add_arguments(self, parser):
        parser.add_argument(
            "query",
            type=str,
            help="Search query",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=5,
            help="Maximum number of results to return (default: 5)",
        )
        parser.add_argument(
            "--threshold",
            type=float,
            default=0.7,
            help="Minimum similarity threshold (0-1, default: 0.7)",
        )

    def handle(self, *args, **options):
        """Run the embeddings search."""
        query = options["query"]
        limit = options["limit"]
        threshold = options["threshold"]

        print(f"\nSearching for pages similar to: {query}\n")
        print("Parameters:")
        print(f"- Max results: {limit}")
        print(f"- Similarity threshold: {threshold}")
        print()

        service = EmbeddingsService()
        results = service.search_similar_pages(query, limit=limit, similarity_threshold=threshold)

        if not results:
            print("No similar pages found.")
            return

        print(f"Found {len(results)} similar pages:\n")
        for page in results:
            print(f"Page: {page.title}")
            print(f"URL: {page.url}")
            print(f"Similarity: {page.similarity:.2%}")
            print(f"Last edited: {page.last_edited_time}")
            print()
