from typing import Any, Dict, Optional

from crewai.tools import BaseTool

from notion.management.commands.base import NotionAPI  # Reuse existing API client


class NotionBaseTool(BaseTool):
    """Base class for all Notion tools"""

    def __init__(self):
        super().__init__()
        self.api = self._initialize_api()

    def _initialize_api(self) -> NotionAPI:
        """Initialize the Notion API client"""
        try:
            return NotionAPI()  # This handles API key from environment
        except Exception as e:
            raise ValueError(f"Failed to initialize Notion API: {str(e)}")

    def _format_response(
        self, success: bool, data: Optional[Any] = None, message: str = "", error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Standardized response format for all tools

        Args:
            success: Whether the operation was successful
            data: Optional data returned by the operation
            message: Human-readable message about the operation
            error: Error message if operation failed

        Returns:
            Dict with standardized response format
        """
        return {"success": success, "message": message, "data": data, "error": error}

    def _get_title_from_page(self, page: Dict[str, Any]) -> str:
        """
        Extract title from a Notion page

        Args:
            page: Notion page object

        Returns:
            Page title as string, "Untitled" if not found
        """
        try:
            title = page.get("properties", {}).get("title", {})
            if not title:
                return "Untitled"
            return "".join(text.get("plain_text", "") for text in title.get("title", [])) or "Untitled"
        except Exception:
            return "Untitled"

    def _handle_api_error(self, e: Exception, operation: str) -> Dict[str, Any]:
        """
        Handle API errors in a consistent way

        Args:
            e: Exception that occurred
            operation: Description of the operation that failed

        Returns:
            Formatted error response
        """
        error_msg = str(e)
        if "401" in error_msg:
            message = "Authentication failed. Please check your API key."
        elif "403" in error_msg:
            message = "Permission denied. Please check your access rights."
        elif "404" in error_msg:
            message = "Resource not found. Please check the ID."
        elif "429" in error_msg:
            message = "Rate limit exceeded. Please try again later."
        else:
            message = f"Failed to {operation}"

        return self._format_response(success=False, error=error_msg, message=message)
