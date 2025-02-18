from typing import Any, Dict, List, Optional


class AdwordsAPIException(Exception):
    """Base exception for Adwords API errors"""

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


class BadRequestError(AdwordsAPIException):
    """400 Bad Request"""

    def __init__(self, message: str, **kwargs):
        super().__init__(400, "bad request", message, **kwargs)


class UnauthorizedError(AdwordsAPIException):
    """401 Unauthorized"""

    def __init__(self, message: str, **kwargs):
        super().__init__(401, "unauthorized", message, **kwargs)


def raise_for_status_code(response_data: Dict[str, Any]) -> None:
    """Raise appropriate exception based on status code"""
    code = response_data.get("code", 500)
    message = response_data.get("message", "Unknown error")
    response_id = response_data.get("response_id")
    data = response_data.get("data", [])
    links = response_data.get("_links", {})

    error_map = {
        400: BadRequestError,
        401: UnauthorizedError,
    }

    error_class = error_map.get(code, AdwordsAPIException)
    raise error_class(message, response_id=response_id, data=data, links=links)
