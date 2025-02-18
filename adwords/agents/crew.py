# import os
# from typing import Dict, List

# from crewai import LLM, Agent, Crew, Process, Task
# from crewai.tools import BaseTool

# from notion.api.client import NotionClient


# class LLMProviders:
#     @staticmethod
#     def get_local_openai():
#         return LLM(model="openai/deepseek-r1-distill-qwen-14b", base_url="http://localhost:1234/v1")

#     @staticmethod
#     def get_deepseek():
#         return LLM(model="deepseek/deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"))

#     @staticmethod
#     def get_chatgpt4():
#         return LLM(model="openai/gpt-4", api_key=os.getenv("OPENAI_API_KEY"))

#     @staticmethod
#     def get_chatgpt4o():
#         return LLM(model="openai/gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))


# class NotionSearchTool(BaseTool):
#     name: str = "search_pages"
#     description: str = "Search for pages in Notion using a query string"

#     def _run(self, query: str) -> List[Dict]:
#         client = NotionClient()
#         return client.search_pages(query)


# class NotionPageTool(BaseTool):
#     name: str = "get_page"
#     description: str = "Retrieve a specific page from Notion using its ID"

#     def _run(self, page_id: str) -> Dict:
#         client = NotionClient()
#         return client.get_page(page_id)


# class NotionCreateTool(BaseTool):
#     name: str = "create_page"
#     description: str = "Create a new page in Notion with specified parent and properties"

#     def _run(self, parent: Dict, properties: Dict) -> Dict:
#         client = NotionClient()
#         return client.create_page(parent=parent, properties=properties)


# class NotionUpdateTool(BaseTool):
#     name: str = "update_page"
#     description: str = "Update an existing page in Notion with new properties"

#     def _run(self, page_id: str, properties: Dict) -> Dict:
#         client = NotionClient()
#         return client.update_page(page_id=page_id, properties=properties)


# class NotionBlocksTool(BaseTool):
#     name: str = "get_blocks"
#     description: str = "Get all blocks from a specific page in Notion"

#     def _run(self, page_id: str) -> List[Dict]:
#         client = NotionClient()
#         return client.get_blocks(page_id)


# class NotionCrew:
#     """Notion organization crew."""

#     def __init__(self):
#         self.llm = LLMProviders.get_chatgpt4o()

#         self.notes_organizer = Agent(
#             role="Notion Notes Organizer",
#             goal="Efficiently organize and manage Notion pages and content",
#             backstory="""You are an expert at organizing and managing digital notes in Notion.
#             Your expertise includes categorizing content, creating structured pages, and maintaining
#             a clean, well-organized workspace.""",
#             verbose=True,
#             tools=[NotionSearchTool(), NotionPageTool(), NotionCreateTool(), NotionUpdateTool(), NotionBlocksTool()],
#             llm=self.llm,
#         )

#     def search_notes(self, query: str) -> Crew:
#         """Search for notes in Notion."""
#         task = Task(
#             description=f"Search for notes matching: {query}",
#             expected_output="A list of matching notes",
#             agent=self.notes_organizer,
#         )

#         return Crew(agents=[self.notes_organizer], tasks=[task], verbose=True, process=Process.sequential, llm=self.llm)

#     def create_note(self, title: str, content: str, parent_id: str = None, database_id: str = None) -> Crew:
#         """Create a new note in Notion.

#         Args:
#             title: The title of the note
#             content: The content of the note
#             parent_id: Optional ID of the parent page
#             database_id: Optional ID of the parent database

#         Either parent_id or database_id must be provided.
#         """
#         if not parent_id and not database_id:
#             raise ValueError("Either parent_id or database_id must be provided")

#         parent = (
#             {"type": "page_id", "page_id": parent_id}
#             if parent_id
#             else {"type": "database_id", "database_id": database_id}
#         )

#         task = Task(
#             description=f"""Create a new note with:
#             Title: {title}
#             Content: {content}
#             Parent: {parent}

#             Steps:
#             1. Create the page with the specified parent and title
#             2. Add the content to the page
#             3. Return the created page details
#             """,
#             expected_output="The created note details",
#             agent=self.notes_organizer,
#         )

#         return Crew(agents=[self.notes_organizer], tasks=[task], verbose=True, process=Process.sequential, llm=self.llm)
