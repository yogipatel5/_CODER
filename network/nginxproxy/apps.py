"""Nginx proxy Django app configuration."""
import importlib
import os
from pathlib import Path

from django.apps import AppConfig


class NginxProxyConfig(AppConfig):
    """Nginx proxy app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "network.nginxproxy"

    def ready(self):
        models_dir = Path(__file__).parent / "models"
        if models_dir.exists():
            for filename in os.listdir(models_dir):
                if filename.endswith(".py"):
                    module_name = os.path.splitext(filename)[0]
                    try:
                        full_module_path = f"nginxproxy.models.{module_name}"
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
                        full_module_path = f"nginxproxy.tasks.{module_name}"
                        importlib.import_module(full_module_path)
                    except ImportError as e:
                        # Handle specific import errors or log them
                        pass

        admin_dir = Path(__file__).parent / "admin"
        if admin_dir.exists():
            for filename in os.listdir(admin_dir):
                if filename.endswith(".py"):
                    module_name = os.path.splitext(filename)[0]
                    try:
                        full_module_path = f"nginxproxy.admin.{module_name}"
                        importlib.import_module(full_module_path)
                    except ImportError as e:
                        # Handle specific import errors or log them
                        pass
