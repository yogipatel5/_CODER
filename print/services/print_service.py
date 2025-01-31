import logging
import os
import tempfile
from typing import Optional

import cups
import requests

from .usb_print_service import USBPrintService

logger = logging.getLogger(__name__)


class PrintService:
    def __init__(self):
        self.cups_conn = cups.Connection()
        self.usb_service = USBPrintService()

    def print_job(self, job) -> Optional[int]:
        """Process a print job"""
        # Route to appropriate printing service based on printer type
        if job.printer.connection_type == "USB":
            return self.usb_service.print_job(job)
        else:
            return self._cups_print_job(job)

    def _cups_print_job(self, job) -> Optional[int]:
        """Process a CUPS print job"""
        try:
            # Mark job as processing
            job = job.__class__.objects.mark_job_started(job.id)

            # Get the file
            file_path = self._download_file(job)

            # Get printer options
            options = {
                "copies": str(job.copies),
                "media": job.paper_size,
                "ColorModel": job.color_mode,
                "Duplex": "DuplexNoTumble" if job.duplex else "None",
            }

            # Add printer-specific options
            if job.custom_settings:
                options.update(job.custom_settings)

            # Special handling for DYMO printers
            if "DYMO" in job.printer.name:
                options.update(
                    {
                        "MediaType": "Auto",
                        "Quality": "Graphics",
                        "LabelWidth": "4 inch",
                        "LabelLength": "6 inch",
                    }
                )
            # Submit print job to CUPS
            cups_job_id = self.cups_conn.printFile(job.printer.device_name, file_path, job.file_name, options)

            # Mark job as completed
            job = job.__class__.objects.mark_job_completed(job.id)

            return cups_job_id

        except Exception as e:
            # Mark job as failed
            job = job.__class__.objects.mark_job_completed(job.id, str(e))
            raise

        finally:
            # Cleanup temp file
            if "file_path" in locals() and not file_path.startswith("/"):
                try:
                    os.unlink(file_path)
                except OSError:
                    logging.error(f"Failed to delete temp file: {file_path}")

    def _download_file(self, job) -> str:
        """Download file from URL to temp file"""
        if job.file_url.startswith("file://"):
            # For local files, just return the path
            return job.file_url.replace("file://", "")

        # For remote URLs, download to temp file
        response = requests.get(job.file_url, stream=True, timeout=(3.05, 27))
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
            return temp_file.name

    def get_printer_status(self, printer) -> dict:
        """Get the current status of a printer"""
        if printer.connection_type == "BLUETOOTH":
            # For Bluetooth printers, we can only check if they're paired
            # You might want to implement actual status checking using bleak
            return {"status": "UNKNOWN", "message": "Status checking not implemented for Bluetooth printers"}
        elif printer.connection_type == "USB":
            # For USB printers, we can only check if they're connected
            # You might want to implement actual status checking using pyusb
            return {"status": "UNKNOWN", "message": "Status checking not implemented for USB printers"}
        else:
            try:
                printers = self.cups_conn.getPrinters()
                if printer.device_name not in printers:
                    return {"status": "OFFLINE", "message": "Printer not found"}

                printer_info = printers[printer.device_name]
                return {
                    "status": "ONLINE" if printer_info["printer-state"] == 3 else "OFFLINE",
                    "state": printer_info.get("printer-state-message", ""),
                    "message": printer_info.get("printer-state-reasons", [""])[0],
                }
            except Exception as e:
                return {"status": "ERROR", "message": str(e)}
