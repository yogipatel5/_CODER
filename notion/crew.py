from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from tools import (
    CreatePageWithMarkdownTool,
    DeletePageTool,
    GetPageInMarkdownTool,
    RetrievePagesTool,
    UpdatePageWithMarkdownTool,
)

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators


@CrewBase
class NotionCrew:
    """TestCrew crew."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools

    # @agent
    # def notes_researcher(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config["notes_researcher"],
    #         verbose=True,
    #         tools=[
    #             RetrievePagesTool(),
    #             CreatePageTool(),
    #             UpdatePageTool(),
    #             DeletePageTool(),
    #             GetPageInMarkdownTool(),
    #             GetPageContentTool(),
    #         ],
    #     )

    @agent
    def notes_organizer(self) -> Agent:
        return Agent(
            config=self.agents_config["notes_organizer"],
            verbose=True,
            tools=[
                RetrievePagesTool(),
                UpdatePageWithMarkdownTool(),
                DeletePageTool(),
                GetPageInMarkdownTool(),
                CreatePageWithMarkdownTool(),
            ],
        )

    @task
    def clean_up_my_notes(self) -> Task:
        return Task(
            config=self.tasks_config["clean_up_my_notes"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the TestCrew crew."""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            verbose=True,
            process=Process.sequential,
        )


if __name__ == "__main__":
    NotionCrew().crew().kickoff()
