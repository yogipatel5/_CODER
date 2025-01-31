import mimetypes
import os
import tempfile
from urllib.parse import urlparse

import requests
from django.core.management.base import BaseCommand, CommandError

from print.models import Printer, PrintJob


class Command(BaseCommand):
    help = "Create a print job from a URL"

    def add_arguments(self, parser):
        parser.add_argument("url", type=str, help="URL of the document to print")
        parser.add_argument("--printer", "-p", type=str, help="Printer alias (e.g., dymo, hp, label) or name")
        parser.add_argument("--copies", "-c", type=int, default=1, help="Number of copies to print")

    def handle(self, *args, **options):
        url = options["url"]
        printer_alias = options["printer"]
        copies = options["copies"]

        # Validate URL
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme == "file":
                # For local files, convert to absolute path
                path = parsed_url.path
                if not os.path.isfile(path):
                    raise CommandError(f"Local file not found: {path}")
            elif not parsed_url.scheme or not parsed_url.netloc:
                # For non-file URLs, require scheme and netloc
                raise CommandError("Invalid URL format")
        except Exception as e:
            raise CommandError(f"Invalid URL: {str(e)}")

        # Get printer
        if printer_alias:
            printer = Printer.objects.get_by_alias(printer_alias)
            if not printer:
                # Try finding by name if alias fails
                try:
                    printer = Printer.objects.get(name__icontains=printer_alias)
                except Printer.DoesNotExist:
                    raise CommandError(
                        f'No printer found with alias or name "{printer_alias}". '
                        "Available printers and their aliases:\n"
                        + "\n".join([f'- {p.name} (aliases: {", ".join(p.aliases)})' for p in Printer.objects.all()])
                    )
        else:
            printer = Printer.objects.get_default_printer()
            if not printer:
                raise CommandError("No default printer configured")

        # Download the file
        try:
            if parsed_url.scheme == "file":
                # For local files, use the file path directly
                file_path = parsed_url.path
                filename = os.path.basename(file_path)
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = "application/octet-stream"
                with open(file_path, "rb") as file:
                    file_data = file.read()
            else:
                response = requests.get(url, stream=True)
                response.raise_for_status()

                # Get content type and filename
                content_type = response.headers.get("content-type", "").split(";")[0]
                content_disp = response.headers.get("content-disposition", "")
                if "filename=" in content_disp:
                    filename = content_disp.split("filename=")[1].strip("\"'")
                else:
                    filename = os.path.basename(urlparse(url).path) or "document"
                    if not filename or filename == "/":
                        filename = "document"

                # Create temp file
                with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            temp_file.write(chunk)
                    temp_file_path = temp_file.name
                file_path = temp_file_path
                file_data = None

            # Create print job
            file_size = os.path.getsize(file_path)

            # Create the print job
            print_job = PrintJob.objects.create_job(
                printer=printer,
                file_name=filename,
                file_type=content_type,
                file_size=file_size,
                file_url=url,
                copies=copies,
                paper_size=printer.default_paper_size,
                color_mode=printer.default_color_model,
                duplex=printer.duplex_capable,
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created print job {print_job.id} for {filename}\n"
                    f"Printer: {printer.name}\n"
                    f"Status: {print_job.status}"
                )
            )

        except requests.exceptions.RequestException as e:
            raise CommandError(f"Failed to download file: {str(e)}")
        except Exception as e:
            raise CommandError(f"Error creating print job: {str(e)}")
        finally:
            # Cleanup temp file
            if "file_path" in locals() and file_path != parsed_url.path:
                try:
                    os.unlink(file_path)
                except OSError:
                    pass
