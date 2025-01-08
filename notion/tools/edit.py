"""Search tool for Notion."""

from crewai.tools import BaseTool


class NotionToolInput(BaseModel):
    """Input schema for NotionTool."""

    page_id: str = Field(..., description="The ID of the page to edit.")
    content: str = Field(..., description="The content to edit the page with.")


class NotionEditPageTool(BaseTool):
    """Edit page tool for Notion."""
