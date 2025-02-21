import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..api.easypost_client import EasyPostClient

if TYPE_CHECKING:
    from ..models import AddressModel, EasyPostAccountModel

logger = logging.getLogger(__name__)


class ShipmentAgent:
    """Agent for creating shipments using EasyPost API."""

    def __init__(self, easypost_account: Optional["EasyPostAccountModel"] = None):
        """Initialize the ShipmentAgent.

        Args:
            easypost_account: Optional EasyPostAccount model instance. If not provided,
                            the default account will be used.
        """
        self.client = EasyPostClient(easypost_account=easypost_account)

    def create_shipment(self, to_address: "AddressModel", parcel_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a shipment using EasyPost API.

        Args:
            to_address: AddressModel instance representing the destination address
            parcel_details: Dictionary containing parcel information with keys:
                          - length: float
                          - width: float
                          - height: float
                          - weight: float (in oz)

        Returns:
            Dict containing the created shipment details from EasyPost

        Raises:
            ValueError: If required data is missing or invalid
            easypost.Error: If EasyPost API request fails
        """
        try:
            # Validate parcel details
            required_fields = ["length", "width", "height", "weight"]
            missing_fields = [f for f in required_fields if f not in parcel_details]
            if missing_fields:
                raise ValueError(f"Missing required parcel details: {', '.join(missing_fields)}")

            # Get default ship-from address
            from_address = self.client.easypost_account.default_ship_from_address.first()
            if not from_address:
                raise ValueError("No default ship-from address set for the EasyPost account")

            # Create shipment through EasyPost client
            shipment = self.client.create_shipment(
                to_address=to_address.to_easypost_dict(),
                from_address=from_address.to_easypost_dict(),
                parcel=parcel_details,
            )

            logger.info(
                "Shipment created successfully",
                extra={
                    "shipment_id": shipment.id,
                    "to_address": to_address.id,
                    "from_address": from_address.id,
                    "easypost_account": self.client.easypost_account.id,
                },
            )

            # Convert shipment to dictionary
            return {
                "id": shipment.id,
                "tracking_code": shipment.tracking_code,
                "status": shipment.status,
                "created_at": shipment.created_at,
                "rates": [
                    {
                        "carrier": rate.carrier,
                        "service": rate.service,
                        "rate": str(rate.rate),
                        "delivery_days": rate.delivery_days,
                    }
                    for rate in shipment.rates
                ],
            }

        except Exception as e:
            logger.error("Failed to create shipment", extra={"error": str(e)})
            raise
