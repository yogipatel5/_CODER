"""Notion crew configuration and setup."""

from pathlib import Path

import yaml
from crewai import Agent, Crew, Task

from notion.tools import NOTION_TOOLS


def get_notion_agent(agent_type: str = "notion_manager", verbose: bool = False) -> Agent:
    """Get a configured Notion agent.

    Args:
        agent_type: Type of agent to create (default: notion_manager)
        verbose: Whether to enable verbose output (default: False)

    Returns:
        Agent: Configured Notion agent
    """
    config_dir = Path(__file__).parent / "config"

    # Load agent config
    with open(config_dir / "agents.yaml", encoding="utf-8") as f:
        agents_config = yaml.safe_load(f)

    agent_config = agents_config[agent_type]

    return Agent(
        role=agent_config["role"],
        goal=agent_config["goal"],
        backstory=agent_config["backstory"],
        verbose=verbose,
        allow_delegation=agent_config.get("allow_delegation", False),
        tools=NOTION_TOOLS,
    )
