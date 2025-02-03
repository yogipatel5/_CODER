# Boiler plate task for sending notifications
import logging

PRIORTY_LOW = "low"
PRIORTY_MEDIUM = "medium"
PRIORTY_HIGH = "high"

logger = logging.getLogger(__name__)


def notify_me(message: str, title: str, priority: str, **kwargs):
    """Send a notification"""
    logger.info(f"Pretend Sending notification: {message}")
    pass
