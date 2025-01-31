import asyncio

from bleak import BleakScanner
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Discover Bluetooth printers and get their addresses"

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str, help="Filter devices by name (e.g., D110)")

    async def discover_devices(self, name_filter=None):
        devices = await BleakScanner.discover()
        for d in devices:
            if name_filter and name_filter.lower() not in d.name.lower():
                continue
            self.stdout.write(f"Found device: {d.name}")
            self.stdout.write(f"  Address: {d.address}")
            self.stdout.write(f"  RSSI: {d.rssi}dBm")
            self.stdout.write("  Details:")
            for key, value in d.details.items():
                self.stdout.write(f"    {key}: {value}")
            self.stdout.write("")

    def handle(self, *args, **options):
        name_filter = options.get("name")
        if name_filter:
            self.stdout.write(f"Looking for devices with name containing '{name_filter}'...")
        else:
            self.stdout.write("Scanning for all Bluetooth devices...")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.discover_devices(name_filter))
