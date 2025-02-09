"""
Show all auto-discovered models, tasks, and signals in the notion app.
"""

import inspect

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Show all auto-discovered models, tasks, and signals in the notion app"

    def _get_models(self):
        """Get all models from the app."""
        app_config = apps.get_app_config("notion")
        return app_config.get_models()

    def _get_tasks(self):
        """Get all Celery tasks from the app."""
        import notion.tasks

        return [
            (name, obj)
            for name, obj in inspect.getmembers(notion.tasks)
            if inspect.isfunction(obj) and hasattr(obj, "delay")
        ]

    def _get_signals(self):
        """Get all signal handlers from the app."""
        import notion.signals

        return [
            (name, obj)
            for name, obj in inspect.getmembers(notion.signals)
            if inspect.isfunction(obj) and hasattr(obj, "is_signal_handler")
        ]

    def handle(self, *args, **options):
        # Show models
        self.stdout.write(self.style.SUCCESS("\nDiscovered Models:"))
        self.stdout.write("================")
        for model in self._get_models():
            self.stdout.write(f"- {model._meta.object_name}")
            # Show fields
            for field in model._meta.fields:
                self.stdout.write(f"  └─ {field.name}: {field.get_internal_type()}")

        # Show tasks
        self.stdout.write(self.style.SUCCESS("\nDiscovered Tasks:"))
        self.stdout.write("================")
        tasks = self._get_tasks()
        if tasks:
            for name, task in tasks:
                self.stdout.write(f"- {name}")
                if task.__doc__:
                    self.stdout.write(f"  └─ {task.__doc__.strip()}")
        else:
            self.stdout.write("  No tasks found")

        # Show signals
        self.stdout.write(self.style.SUCCESS("\nDiscovered Signals:"))
        self.stdout.write("================")
        signals = self._get_signals()
        if signals:
            for name, handler in signals:
                self.stdout.write(f"- {name}")
                if handler.__doc__:
                    self.stdout.write(f"  └─ {handler.__doc__.strip()}")
        else:
            self.stdout.write("  No signal handlers found")
