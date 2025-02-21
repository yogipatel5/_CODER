import logging
from typing import TYPE_CHECKING, Any, Dict, Tuple

import easypost
from django.core.exceptions import ValidationError

if TYPE_CHECKING:
    from shipper.models import EasyPostAccountModel

logger = logging.getLogger(__name__)


class EasyPostClient:
    """Client for interacting with the EasyPost API"""

    def __init__(self, easypost_account: "EasyPostAccountModel" = None):
        """Initialize the EasyPost client.

        Args:
            easypost_account: EasyPostAccount model instance to use for API key
        """
        if not easypost_account:
            # Import here to avoid circular import
            from shipper.models import EasyPostAccountModel

            easypost_account = EasyPostAccountModel.objects.get_default_account()
            if not easypost_account:
                raise ValueError("No default EasyPost account available")

        # Import here to avoid circular import
        from shipper.models import EasyPostAccountModel

        api_key = EasyPostAccountModel.objects.get_api_key(easypost_account)
        self.client = easypost.EasyPostClient(api_key=api_key)
        self.easypost_account = easypost_account

    @staticmethod
    def validate_api_key(api_key: str, is_test: bool = False) -> Tuple[bool, str]:
        """
        Validates an EasyPost API key by attempting to retrieve the account.

        Args:
            api_key (str): The API key to validate
            is_test (bool): Whether this is a test API key

        Returns:
            Tuple[bool, str]: A tuple containing:
                - bool: True if valid, False if invalid
                - str: Account ID if valid, error message if invalid
        """
        try:
            # For test keys, we'll create a test client
            client = easypost.EasyPostClient(api_key=api_key)

            # Try to do a simple operation that works with both test and prod keys
            if is_test:
                # For test keys, we'll try to create a test address which should work
                client.address.create(
                    street1="417 MONTGOMERY ST",
                    street2="FLOOR 5",
                    city="SAN FRANCISCO",
                    state="CA",
                    zip="94104",
                    country="US",
                    company="EasyPost",
                    phone="415-123-4567",
                )
                return True, "test_verified"
            else:
                # For production keys, verify account access
                account = client.user.retrieve_me()
                return True, account.id

        except Exception as e:
            logger.error(f"Failed to validate API key: {str(e)}")
            return False, str(e)

    def create_shipment(self, to_address: Dict[str, Any], from_address: Dict[str, Any], parcel: Dict[str, Any]) -> Any:
        """Create a shipment using EasyPost API.

        Args:
            to_address: Dictionary containing destination address details
            from_address: Dictionary containing sender address details
            parcel: Dictionary containing parcel dimensions and weight

        Returns:
            The created shipment object from EasyPost

        Raises:
            easypost.Error: If the API request fails
        """
        try:
            shipment = self.client.shipment.create(to_address=to_address, from_address=from_address, parcel=parcel)
            return shipment

        except Exception as e:
            logger.error(f"Failed to create shipment: {str(e)}")
            raise
