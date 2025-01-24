import importlib
import os
from pathlib import Path

from django.apps import AppConfig


class PfsenseConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "network.pfsense"

    def ready(self):
        import network.pfsense.tasks  # noqa: F401

        # Dynamically import all models from the 'models' directory
        models_dir = Path(__file__).parent / "models"
        if models_dir.exists():
            for filename in os.listdir(models_dir):
                if filename.endswith(".py"):
                    module_name = os.path.splitext(filename)[0]
                    try:
                        full_module_path = f"network.pfsense.models.{module_name}"
                        importlib.import_module(full_module_path)
                    except ImportError as e:
                        # Handle specific import errors or log them
                        pass

        tasks_dir = Path(__file__).parent / "tasks"
        if tasks_dir.exists():
            for filename in os.listdir(tasks_dir):
                if filename.endswith(".py"):
                    module_name = os.path.splitext(filename)[0]
                    try:
                        full_module_path = f"network.pfsense.tasks.{module_name}"
                        importlib.import_module(full_module_path)
                    except ImportError as e:
                        # Handle specific import errors or log them
                        pass
