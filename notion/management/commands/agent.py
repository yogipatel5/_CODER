"""
Command to run Notion agent tasks.
"""

import logging
import os
from pathlib import Path

import yaml
from crewai import Agent, Crew, Task
from django.core.management.base import BaseCommand, CommandError
from dotenv import load_dotenv

from .base import NOTION_TOOLS

load_dotenv()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Django management command for interacting with Notion agents.

    This command allows users to interact with different types of Notion agents
    (manager, researcher, editor) by providing prompts and receiving responses.
    The agents use CrewAI for task execution and the Notion API for workspace operations.
    """

    help = "Interact with Notion agent"

    def add_arguments(self, parser):
        parser.add_argument("prompt", help="The prompt to send to the agent")
        parser.add_argument(
            "--agent",
            default="notion_manager",
            choices=["notion_manager", "notion_researcher", "notion_editor"],
            help="The type of agent to use",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Enable verbose output",
        )

    def handle(self, *args, **options):
        try:
            config_dir = Path(__file__).parent.parent.parent / "config"

            # Load agent config
            with open(config_dir / "agents.yaml", encoding="utf-8") as f:
                agents_config = yaml.safe_load(f)

            agent_config = agents_config[options["agent"]]

            # Create agent with tools
            agent = Agent(
                role=agent_config["role"],
                goal=agent_config["goal"],
                backstory=agent_config["backstory"],
                verbose=agent_config.get("verbose", True),
                allow_delegation=agent_config.get("allow_delegation", False),
                tools=NOTION_TOOLS,
            )

            # Create task with expected output
            task = Task(
                description=options["prompt"],
                expected_output="A detailed response about the requested Notion operation",
                agent=agent,
            )

            # Create crew with single agent and task
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=options["verbose"],
            )

            # Execute task and get result
            result = crew.kickoff()
            self.stdout.write(f"Task completed: {result}")

        except Exception as e:
            error_msg = str(e)
            self.stdout.write(f"Error: {error_msg}")
            raise CommandError(error_msg) from e
