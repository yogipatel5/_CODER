"""
Test command for Notion Crew AI with local LLM.
"""

from django.core.management.base import BaseCommand

from notion.agents.crew import NotionCrew


class Command(BaseCommand):
    help = "Test Notion Crew AI with local LLM"

    def add_arguments(self, parser):
        parser.add_argument(
            "--query", type=str, help="Query to search for in Notion", default="What are my recent tasks?"
        )
        parser.add_argument(
            "--create",
            action="store_true",
            help="Create a test note",
        )
        parser.add_argument(
            "--database-id",
            type=str,
            help="Database ID for creating notes",
        )

    def handle(self, *args, **options):
        self.stdout.write("Initializing Notion Crew with local LLM...")
        crew = NotionCrew()

        if options["create"] and options["database_id"]:
            self.stdout.write("Creating a test note...")
            test_crew = crew.create_note(
                title="Test Note from Local LLM",
                content="This is a test note created by the Crew AI using a local LLM.",
                database_id=options["database_id"],
            )
            result = test_crew.kickoff()
            self.stdout.write(self.style.SUCCESS(f"Create note result: {result}"))
        else:
            self.stdout.write(f"Searching Notion with query: {options['query']}")
            search_crew = crew.search_notes(options["query"])
            result = search_crew.kickoff()
            self.stdout.write(self.style.SUCCESS(f"Search result: {result}"))
