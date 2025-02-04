"""Auto-discover and import all tasks in this directory."""

import importlib
import inspect
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Get all .py files in the tasks directory
tasks_dir = Path(__file__).parent
task_files = [
    f.stem for f in tasks_dir.glob("*.py") if f.is_file() and f.stem != "__init__" and not f.stem.startswith("base_")
]

# Import each task file and get all task functions
for module_name in task_files:
    try:
        module = importlib.import_module(f"pfsense.tasks.{module_name}")

        # Get all functions from the module that are Celery tasks
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isfunction(obj)
                and hasattr(obj, "delay")  # Check if it's a Celery task
                and obj.__module__ == f"pfsense.tasks.{module_name}"
            ):
                # Add the task to this module's namespace
                globals()[name] = obj
                logger.debug(f"Imported task {name} from {module_name}")
    except Exception as e:
        logger.error(f"Failed to import tasks from {module_name}: {str(e)}")
