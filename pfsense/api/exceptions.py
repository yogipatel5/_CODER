from typing import Any, Dict, List, Optional


class PFSenseAPIException(Exception):
    """Base exception for PFSense API errors"""

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


class BadRequestError(PFSenseAPIException):
    """400 Bad Request"""

    def __init__(self, message: str, **kwargs):
        super().__init__(400, "bad request", message, **kwargs)


class UnauthorizedError(PFSenseAPIException):
    """401 Unauthorized"""

    def __init__(self, message: str, **kwargs):
        super().__init__(401, "unauthorized", message, **kwargs)


class ForbiddenError(PFSenseAPIException):
    """403 Forbidden"""

    def __init__(self, message: str, **kwargs):
        super().__init__(403, "forbidden", message, **kwargs)


class NotFoundError(PFSenseAPIException):
    """404 Not Found"""

    def __init__(self, message: str, **kwargs):
        super().__init__(404, "not found", message, **kwargs)


class MethodNotAllowedError(PFSenseAPIException):
    """405 Method Not Allowed"""

    def __init__(self, message: str, **kwargs):
        super().__init__(405, "method not allowed", message, **kwargs)


class NotAcceptableError(PFSenseAPIException):
    """406 Not Acceptable"""

    def __init__(self, message: str, **kwargs):
        super().__init__(406, "not acceptable", message, **kwargs)


class ConflictError(PFSenseAPIException):
    """409 Conflict"""

    def __init__(self, message: str, **kwargs):
        super().__init__(409, "conflict", message, **kwargs)


class UnsupportedMediaTypeError(PFSenseAPIException):
    """415 Unsupported Media Type"""

    def __init__(self, message: str, **kwargs):
        super().__init__(415, "unsupported media type", message, **kwargs)


class UnprocessableEntityError(PFSenseAPIException):
    """422 Unprocessable Entity"""

    def __init__(self, message: str, **kwargs):
        super().__init__(422, "unprocessable entity", message, **kwargs)


class FailedDependencyError(PFSenseAPIException):
    """424 Failed Dependency"""

    def __init__(self, message: str, **kwargs):
        super().__init__(424, "failed dependency", message, **kwargs)


class InternalServerError(PFSenseAPIException):
    """500 Internal Server Error"""

    def __init__(self, message: str, **kwargs):
        super().__init__(500, "internal server error", message, **kwargs)


class ServiceUnavailableError(PFSenseAPIException):
    """503 Service Unavailable"""

    def __init__(self, message: str, **kwargs):
        super().__init__(503, "service unavailable", message, **kwargs)


def raise_for_status_code(response_data: Dict[str, Any]) -> None:
    """Raise appropriate exception based on status code"""
    code = response_data.get("code", 500)
    message = response_data.get("message", "Unknown error")
    response_id = response_data.get("response_id")
    data = response_data.get("data", [])
    links = response_data.get("_links", {})
    kwargs = {"response_id": response_id, "data": data, "links": links}

    error_map = {
        400: BadRequestError,
        401: UnauthorizedError,
        403: ForbiddenError,
        404: NotFoundError,
        405: MethodNotAllowedError,
        406: NotAcceptableError,
        409: ConflictError,
        415: UnsupportedMediaTypeError,
        422: UnprocessableEntityError,
        424: FailedDependencyError,
        500: InternalServerError,
        503: ServiceUnavailableError,
    }

    if code >= 400:
        exception_class = error_map.get(code, PFSenseAPIException)
        raise exception_class(message, **kwargs)
