import subprocess

from django.core.management.base import BaseCommand

from print.models.printer import (
    ColorModel,
    MediaType,
    PaperSize,
    Printer,
    PrinterStatus,
    PrinterType,
    PrintQuality,
)


class Command(BaseCommand):
    help = "Import printers from CUPS"

    def _get_printer_info(self, printer_name):
        """Get detailed printer info using lpoptions"""
        try:
            result = subprocess.run(["lpoptions", "-p", printer_name, "-l"], capture_output=True, text=True, check=True)
            options = {}
            for line in result.stdout.split("\n"):
                if not line:
                    continue
                key = line.split("/", 1)[0]
                options[key] = line
            return options
        except subprocess.CalledProcessError:
            self.stdout.write(self.style.WARNING(f"Could not get options for {printer_name}"))
            return {}

    def handle(self, *args, **options):
        # Get list of printers
        result = subprocess.run(["lpstat", "-p", "-d"], capture_output=True, text=True)

        # Get default printer
        default_printer = None
        for line in result.stdout.split("\n"):
            if "system default destination" in line:
                default_printer = line.split(": ")[-1]
                break

        # Process each printer
        for line in result.stdout.split("\n"):
            if not line.startswith("printer "):
                continue

            # Parse printer info
            printer_name = line.split()[1]
            status = "idle" if "is idle" in line else "offline"

            # Get detailed options
            options = self._get_printer_info(printer_name)

            # Determine printer type and settings based on name
            is_dymo = "DYMO" in printer_name
            printer_data = {
                "name": printer_name.replace("_", " "),
                "device_name": printer_name,
                "printer_type": PrinterType.THERMAL if is_dymo else PrinterType.INKJET,
                "status": PrinterStatus.IDLE if status == "idle" else PrinterStatus.OFFLINE,
                "is_default": printer_name == default_printer,
                "location": "Yogi's Mac Studio" if is_dymo else "Network Printer",
                "model": "LabelWriter 4XL" if is_dymo else "OfficeJet Pro 8720",
                "airprint_enabled": not is_dymo,
                "color_capable": not is_dymo,
                "duplex_capable": not is_dymo,
                "default_paper_size": PaperSize.LABEL_4X6 if is_dymo else PaperSize.LETTER,
                "default_media_type": MediaType.LABELS if is_dymo else MediaType.ANY,
                "default_print_quality": PrintQuality.TEXT if is_dymo else PrintQuality.NORMAL,
                "default_color_model": ColorModel.GRAY if is_dymo else ColorModel.RGB,
                "resolution_dpi": 300 if is_dymo else 1200,
                "supports_custom_paper_size": True if is_dymo else False,
                "cups_options": options,
            }

            # Create or update printer
            printer, created = Printer.objects.update_or_create(device_name=printer_name, defaults=printer_data)

            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} printer {printer.name}"))
