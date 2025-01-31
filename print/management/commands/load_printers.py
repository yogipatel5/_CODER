from pathlib import Path

import yaml
from django.core.management.base import BaseCommand

from print.models.printer import Printer


class Command(BaseCommand):
    help = "Load printers from printers.yaml configuration file"

    def handle(self, *args, **options):
        # Get the path to the YAML file
        yaml_path = Path(__file__).resolve().parent.parent.parent / "printers.yaml"

        if not yaml_path.exists():
            self.stdout.write(self.style.ERROR(f"Configuration file not found: {yaml_path}"))
            return

        # Load the YAML configuration
        try:
            with open(yaml_path, "r") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.stdout.write(self.style.ERROR(f"Error parsing YAML file: {e}"))
            return

        # Process each printer in the configuration
        for printer_data in config["printers"]:
            printer, created = Printer.objects.update_or_create(
                device_name=printer_data["device_name"], defaults=printer_data
            )

            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} printer {printer.name}"))
