"""Admin configuration for shipper app."""

import importlib
import logging
from pathlib import Path

from django.contrib import admin

from shared.admin import SharedTaskAdmin, SharedTaskErrorAdmin
from shipper.models import Task, TaskError

from .easypost_admin import EasyPostAccountAdmin

# Register Task with SharedTaskAdmin
admin.site.register(Task, SharedTaskAdmin)
admin.site.register(TaskError, SharedTaskErrorAdmin)
"""Auto-discover and import all admin classes in this directory."""
__all__ = ["SharedTaskAdmin", "SharedTaskErrorAdmin", "EasyPostAccountAdmin"]

logger = logging.getLogger(__name__)

# Get all .py files in the admin directory
admin_dir = Path(__file__).parent
admin_files = [f.stem for f in admin_dir.glob("*.py") if f.is_file() and f.stem != "__init__"]

# Import each admin file
for module_name in admin_files:
    try:
        importlib.import_module(f"shipper.admin.{module_name}")
        logger.debug(f"Imported admin module {module_name}")
    except Exception as e:
        logger.error(f"Failed to import admin module {module_name}: {str(e)}")
