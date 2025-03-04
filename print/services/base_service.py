"""Base service for print."""

import logging

logger = logging.getLogger(__name__)


class BaseService:
    """Base service class with common functionality."""

    def __init__(self):
        """Initialize the service."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def log_error(self, message: str, error: Exception = None):
        """Log an error with consistent formatting."""
        if error:
            self.logger.error(f"{message}: {str(error)}")
        else:
            self.logger.error(message)

    def log_info(self, message: str):
        """Log an info message with consistent formatting."""
        self.logger.info(message)

    def log_debug(self, message: str):
        """Log a debug message with consistent formatting."""
        self.logger.debug(message)
