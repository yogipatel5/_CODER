import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from ...agents.shipment_agent import ShipmentAgent
from ...models import AddressModel


class Command(BaseCommand):
    help = "Create a shipment using EasyPost"

    def add_arguments(self, parser):
        parser.add_argument("--address-id", type=int, help="ID of the existing address to ship to")
        parser.add_argument(
            "--parcel", type=str, help="JSON string containing parcel details (length, width, height, weight)"
        )

    def handle(self, *args, **options):
        try:
            # Validate inputs
            if not options["address_id"]:
                raise CommandError("--address-id is required")
            if not options["parcel"]:
                raise CommandError("--parcel is required")

            # Get address
            try:
                address = AddressModel.objects.get(id=options["address_id"])
            except AddressModel.DoesNotExist:
                raise CommandError(f'Address with ID {options["address_id"]} does not exist')

            # Parse parcel details
            try:
                parcel_details = json.loads(options["parcel"])
            except json.JSONDecodeError:
                raise CommandError("Invalid JSON format for parcel details")

            # Create shipment
            agent = ShipmentAgent()
            result = agent.create_shipment(to_address=address, parcel_details=parcel_details)

            # Output results
            self.stdout.write(self.style.SUCCESS("Shipment created successfully!"))
            self.stdout.write(json.dumps(result, indent=2))

        except ValidationError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f"Error creating shipment: {str(e)}")
