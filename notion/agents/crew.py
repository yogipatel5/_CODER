from crewai import LLM, Agent, Crew, Process, Task
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

llm = LLM(model="anthropic/claude-3-sonnet-20240229-v1:0", temperature=0.7)


@CrewBase
class NotionCrew:
    """Notion organization crew."""

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
    def analyze_note(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_note"],
        )

    @task
    def process_note(self) -> Task:
        return Task(
            config=self.tasks_config["process_note"],
        )

    @task
    def categorize_and_move(self) -> Task:
        return Task(
            config=self.tasks_config["categorize_and_move"],
        )

    @task
    def combine_related_notes(self) -> Task:
        return Task(
            config=self.tasks_config["combine_related_notes"],
        )

    @task
    def cleanup_originals(self) -> Task:
        return Task(
            config=self.tasks_config["cleanup_originals"],
        )

    @task
    def manage_workspace(self) -> Task:
        return Task(
            config=self.tasks_config["manage_workspace"],
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Notion organization crew."""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            verbose=True,
            process=Process.sequential,
            llm=llm,
        )


if __name__ == "__main__":
    NotionCrew().crew().kickoff()
