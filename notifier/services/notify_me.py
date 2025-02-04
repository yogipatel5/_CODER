# Boiler plate task for sending notifications
import logging

PRIORITY_LOW = "low"
PRIORITY_MEDIUM = "medium"
PRIORITY_HIGH = "high"

logger = logging.getLogger(__name__)


class NotifyMeTask:
    """Task to send notifications"""

    @staticmethod
    def notify_me(message: str, title: str, priority: str, **kwargs):
        """Send a notification"""
        logger.info(f"Pretend Sending notification: {message}")
        pass
