"""Dynamic router for Celery tasks based on Django app structure."""

import re
from typing import Any, Dict, Optional

from django.conf import settings
from kombu import Exchange, Queue


class DjangoAppRouter:
    """Routes Celery tasks based on Django app structure."""

    def __init__(self):
        """Initialize router with app configs and queues."""
        self.app_configs = getattr(settings, "CELERY_APP_CONFIGS", {})
        self.default_queue = getattr(settings, "CELERY_DEFAULT_QUEUE", "default")

        # Create queues dynamically
        self._queues = {}
        for app_name in self.app_configs:
            queue_name = f"{app_name}_queue"
            self._queues[app_name] = Queue(
                queue_name,
                Exchange(queue_name, type="direct"),
                routing_key=queue_name,
            )

    def get_app_name(self, task_name: str) -> Optional[str]:
        """Extract app name from task name (e.g., 'pfsense.tasks.sync_dhcp_routes' -> 'pfsense')."""
        match = re.match(r"^([^.]+)", task_name)
        return match.group(1) if match else None

    def route_for_task(self, task_name: str, *args: Any, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Route tasks based on their app name.

        Args:
            task_name: Full task name (e.g., 'pfsense.tasks.sync_dhcp_routes')

        Returns:
            Dict containing routing options or None for default routing
        """
        app_name = self.get_app_name(task_name)
        if not app_name or app_name not in self.app_configs:
            return None

        queue_name = f"{app_name}_queue"
        return {
            "queue": queue_name,
            "exchange": queue_name,
            "routing_key": queue_name,
        }
