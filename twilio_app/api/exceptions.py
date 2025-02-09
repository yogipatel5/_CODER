from typing import Any, Dict, List, Optional


class TwilioAPIException(Exception):
    """Base exception for Twilio API errors"""

    def __init__(
        self,
        code: int,
        status: str,
        message: str,
        response_id: Optional[str] = None,
        data: Optional[List[Dict[str, Any]]] = None,
        links: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.status = status
        self.message = message
        self.response_id = response_id
        self.data = data or []
        self.links = links or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary format"""
        return {
            "code": self.code,
            "status": self.status,
            "response_id": self.response_id,
            "message": self.message,
            "data": self.data,
            "_links": self.links,
        }


class UnauthorizedError(TwilioAPIException):
    """401 Unauthorized"""

    def __init__(self, message: str, **kwargs):
        super().__init__(401, "unauthorized", message, **kwargs)
