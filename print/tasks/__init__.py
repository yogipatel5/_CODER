"""
Task auto-discovery module. This module automatically imports all Celery tasks
from the tasks directory, excluding base classes and __init__.py.
"""

import importlib
import inspect
from pathlib import Path

# Get all .py files in the tasks directory
tasks_dir = Path(__file__).parent
task_files = [f.stem for f in tasks_dir.glob("*.py") if f.is_file() and f.stem not in {"__init__", "base_task"}]

# Import each task file and get all celery tasks
for module_name in task_files:
    module = importlib.import_module(f"print.tasks.{module_name}")

    # Get all functions from the module that are celery tasks
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and hasattr(obj, "delay"):  # celery tasks have .delay()
            # Add the task to this module's namespace
            globals()[name] = obj

# Prevent importing base_task from print.tasks
__all__ = list(name for name, obj in globals().items() if inspect.isfunction(obj) and hasattr(obj, "delay"))

# Clean up namespace
del Path, importlib, inspect, tasks_dir, task_files
