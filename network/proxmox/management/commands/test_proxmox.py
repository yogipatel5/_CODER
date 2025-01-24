"""
Management command to test Proxmox connection.
"""

from django.core.management.base import BaseCommand

from network.proxmox.api.client import ProxmoxClient


class Command(BaseCommand):
    help = "Test connection to Proxmox server"

    def handle(self, *args, **options):
        client = ProxmoxClient()
        if client.test_connection():
            self.stdout.write(self.style.SUCCESS("Successfully connected to Proxmox server"))
        else:
            self.stdout.write(self.style.ERROR("Failed to connect to Proxmox server"))
