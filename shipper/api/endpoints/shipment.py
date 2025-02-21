"""
Shipment endpoint client for creating and managing shipments.
"""

from typing import Any, Dict

from django.core.exceptions import ValidationError

from ...agents.shipment_agent import ShipmentAgent
from ...models import AddressModel
from ..client import APIClient
from ..exceptions import APIError


class ShipmentEndpoint:
    """Client for interacting with shipment-related endpoints."""

    def __init__(self, client: APIClient):
        self.client = client
        self.base_path = "/api/v1/shipments"

    def create_shipment(self, address_id: int, parcel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new shipment.

        Args:
            address_id: ID of the destination address
            parcel_details: Dictionary containing parcel dimensions and weight

        Returns:
            Created shipment data

        Raises:
            ValidationError: If input data is invalid
            APIError: If the API request fails
        """
        try:
            # Validate address
            try:
                address = AddressModel.objects.get(id=address_id)
            except AddressModel.DoesNotExist:
                raise ValidationError(f"Address with ID {address_id} does not exist")

            # Create shipment using agent
            agent = ShipmentAgent()
            result = agent.create_shipment(to_address=address, parcel_details=parcel_details)
            return result

        except ValidationError:
            raise
        except Exception as e:
            raise APIError(f"Failed to create shipment: {str(e)}")
