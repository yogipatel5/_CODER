import logging
from typing import Tuple

import easypost
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


class EasyPostClient:
    """Client for interacting with the EasyPost API"""

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
            logger.error(f"EasyPost API key validation failed: {str(e)}")
            return False, str(e)
