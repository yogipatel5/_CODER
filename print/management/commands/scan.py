from django.core.management.base import BaseCommand
from django.utils import timezone
import requests
import time
from pathlib import Path
from ...models import Printer


class Command(BaseCommand):
    help = "Trigger a scan job on HP OfficeJet Pro 8720"

    def add_arguments(self, parser):
        parser.add_argument(
            "--format", type=str, default="pdf", choices=["pdf", "jpg"], help="Output format (default: pdf)"
        )
        parser.add_argument(
            "--resolution",
            type=str,
            default="300",
            choices=["75", "100", "200", "300"],
            help="Scan resolution in DPI (default: 300)",
        )
        parser.add_argument(
            "--color", type=str, default="Color", choices=["Color", "Gray"], help="Color mode (default: Color)"
        )

    def handle(self, *args, **options):
        try:
            # Get the first printer (assuming it's the HP OfficeJet Pro 8720)
            printer = Printer.objects.filter(is_default=True).first() or Printer.objects.first()

            if not printer:
                self.stdout.write(self.style.ERROR("No printers found in the database"))
                return

            if not printer.ip_address:
                self.stdout.write(self.style.ERROR(f"No IP address set for printer: {printer.name}"))
                return

            printer_ip = printer.ip_address
            self.stdout.write(f"Using printer: {printer.name} at {printer_ip}")

            # Check if scanner is ready
            try:
                scanner_status = requests.get(
                    f"http://{printer_ip}/eSCL/ScannerStatus", headers={"Accept": "application/json"}, timeout=5
                )
                if scanner_status.status_code != 200:
                    self.stdout.write(
                        self.style.ERROR(
                            "Scanner is not ready. Please check if the scanner lid is closed and paper is loaded."
                        )
                    )
                    return
            except requests.exceptions.RequestException as e:
                self.stdout.write(self.style.ERROR(f"Could not connect to scanner: {str(e)}"))
                return

            # Prepare scan settings XML
            scan_settings = f"""<?xml version="1.0" encoding="UTF-8"?>
<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03">
    <scan:Intent>Document</scan:Intent>
    <scan:InputSource>Platen</scan:InputSource>
    <scan:ColorMode>{options['color']}</scan:ColorMode>
    <scan:DocumentFormat>{options['format'].upper()}</scan:DocumentFormat>
    <scan:XResolution>{options['resolution']}</scan:XResolution>
    <scan:YResolution>{options['resolution']}</scan:YResolution>
    <scan:SaveToNetwork>true</scan:SaveToNetwork>
    <scan:SavePath>Scans</scan:SavePath>
</scan:ScanSettings>"""

            # Start scan job
            self.stdout.write("Initiating scan...")
            response = requests.post(
                f"http://{printer_ip}/eSCL/ScanJobs",
                data=scan_settings,
                headers={"Content-Type": "application/xml", "Accept": "application/json"},
                timeout=5,
            )

            if response.status_code not in [201, 202]:
                self.stdout.write(self.style.ERROR(f"Failed to start scan. Status code: {response.status_code}"))
                try:
                    error_details = response.json()
                    self.stdout.write(self.style.ERROR(f"Error details: {error_details}"))
                except:
                    self.stdout.write(self.style.ERROR(f"Response: {response.text}"))
                return

            # Get job location from response headers
            job_location = response.headers.get("Location")
            if not job_location:
                self.stdout.write(self.style.ERROR("No job location returned from printer"))
                return

            self.stdout.write("Scan job started. Monitoring progress...")

            # Monitor scan progress
            while True:
                try:
                    status_response = requests.get(
                        f"http://{printer_ip}{job_location}", headers={"Accept": "application/json"}, timeout=5
                    )

                    if status_response.status_code == 200:
                        status = status_response.json().get("Status", {}).get("State", "")

                        if status.lower() == "completed":
                            self.stdout.write(
                                self.style.SUCCESS("Scan completed successfully! File saved to network share: Scans")
                            )
                            break
                        elif status.lower() == "failed":
                            error = status_response.json().get("Status", {}).get("Error", "Unknown error")
                            self.stdout.write(self.style.ERROR(f"Scan failed: {error}"))
                            break
                        elif status.lower() in ["processing", "pending"]:
                            self.stdout.write("Scanning in progress...")
                            time.sleep(2)
                        else:
                            self.stdout.write(f"Unknown status: {status}")
                            break
                    else:
                        self.stdout.write(self.style.ERROR(f"Failed to get job status: {status_response.text}"))
                        break
                except requests.exceptions.RequestException as e:
                    self.stdout.write(self.style.ERROR(f"Error checking job status: {str(e)}"))
                    break

        except requests.exceptions.ConnectionError:
            self.stdout.write(
                self.style.ERROR(f"Could not connect to printer at {printer_ip}. Please verify the network connection.")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during scanning: {str(e)}"))
