from typing import Optional


class NotionError(Exception):
    """Base error class for Notion API errors."""

    def __init__(
        self,
        message: str,
        error_type: str = "unknown",
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ):
        """Initialize NotionError.

        Args:
            message: Error message.
            error_type: Type of error (e.g., "validation", "authentication", "permission").
            status_code: HTTP status code.
            error_code: Error code from Notion API.
        """
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.error_code = error_code

    def __str__(self) -> str:
        """Return string representation of error."""
        return f"{self.error_type.upper()}: {self.message}"

    @classmethod
    def from_api_error(cls, error: dict) -> "NotionError":
        """Create NotionError from Notion API error response.

        Args:
            error: Error response from Notion API.

        Returns:
            NotionError instance.
        """
        message = error.get("message", "Unknown error")
        error_code = error.get("code")
        status = error.get("status")

        error_type = "unknown"
        if status == 401:
            error_type = "authentication"
        elif status == 403:
            error_type = "permission"
        elif status == 404:
            error_type = "not_found"
        elif status == 429:
            error_type = "rate_limited"
        elif status == 400:
            error_type = "validation"
        elif status == 500:
            error_type = "server_error"

        return cls(
            message=message,
            error_type=error_type,
            status_code=status,
            error_code=error_code,
        )
