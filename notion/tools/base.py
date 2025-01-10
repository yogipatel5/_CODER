"""
Base tool for Notion operations.
"""

from typing import Any, ClassVar, Dict, Optional, Type

from pydantic import BaseModel, ValidationError

from notion.tools.errors import NotionError


class NotionBaseTool:
    """Base class for Notion tools."""

    name: ClassVar[str] = ""
    description: ClassVar[str] = ""
    args_schema: ClassVar[Type[BaseModel]] = BaseModel

    def __init__(self, api: Optional[Any] = None):
        """Initialize tool with optional API client."""
        self.api = api or self._initialize_api()

    def _initialize_api(self) -> Any:
        """Initialize API client."""
        try:
            from notion.management.commands.base import NotionAPI

            return NotionAPI()
        except Exception as e:
            raise NotionError(f"Failed to initialize API client: {e}")

    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """Run the tool with the given arguments."""
        try:
            # Validate input arguments
            args = self.args_schema(**kwargs)
            return self._run(**args.model_dump())
        except Exception as e:
            if isinstance(e, ValidationError):
                return self._format_response(
                    success=False,
                    message="Validation error",
                    error=str(e),
                )
            return self._handle_api_error(e, "run operation")

    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """Implement tool-specific logic."""
        raise NotImplementedError

    def _format_response(
        self,
        success: bool,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Format tool response."""
        return {
            "success": success,
            "message": message,
            "data": data,
            "error": error,
        }

    def _get_title_from_page(self, page: Dict[str, Any]) -> str:
        """Extract title from page properties."""
        try:
            properties = page.get("properties", {})
            title_property = properties.get("title", {})
            title_content = title_property.get("title", [])
            if title_content and "plain_text" in title_content[0]:
                return title_content[0]["plain_text"]
        except (KeyError, IndexError, AttributeError):
            pass
        return "Untitled"

    def _handle_api_error(self, error: Exception, action: str) -> Dict[str, Any]:
        """Handle API errors."""
        error_str = str(error).lower()
        message = f"Failed to {action}"

        if "unauthorized" in error_str or "authentication" in error_str:
            message += " due to authentication error"
        elif "forbidden" in error_str or "permission" in error_str:
            message += " due to insufficient permissions"
        elif "not found" in error_str:
            message += " - resource not found"
        elif "rate limit" in error_str:
            message += " due to rate limit"
        elif "validation" in error_str:
            message += " due to validation error"
        else:
            message += f" due to error: {error}"

        return {
            "success": False,
            "message": message,
            "error": str(error),
        }
