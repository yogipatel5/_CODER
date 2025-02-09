import logging
import os
from typing import Any, Dict, Optional

import twilio.rest as twilio_rest
from twilio.base.exceptions import TwilioRestException

from .exceptions import TwilioAPIException, UnauthorizedError

logger = logging.getLogger(__name__)


class TwilioClientManager:
    """Manager class for handling multiple Twilio accounts and their credentials"""

    def __init__(self):
        self._clients: Dict[str, twilio_rest.Client] = {}

    def get_client(self, account_name: str) -> twilio_rest.Client:
        """
        Get or create a Twilio client for the specified account.

        Args:
            account_name: The friendly name of the Twilio account

        Returns:
            A configured Twilio client instance

        Raises:
            TwilioAPIException: If the account doesn't exist or credentials can't be retrieved
        """
        if account_name in self._clients:
            return self._clients[account_name]

        # Import here to avoid circular import
        from ..models import TwilioAccount

        try:
            account = TwilioAccount.objects.get(name=account_name, is_active=True)
        except TwilioAccount.DoesNotExist:
            raise TwilioAPIException(404, "not found", f"Twilio account '{account_name}' not found or is inactive")

        try:
            # Get auth token from environment variables
            auth_token = os.getenv(f"{account.vault_auth_token_path.upper()}_AUTH_TOKEN")
            if not auth_token:
                raise UnauthorizedError(f"Could not retrieve auth token for path: {account.vault_auth_token_path}")

            # Create new client instance
            client = twilio_rest.Client(account.account_sid, auth_token)
            self._clients[account_name] = client
            return client

        except Exception as e:
            logger.error(f"Error initializing Twilio client for account {account_name}: {str(e)}")
            raise TwilioAPIException(500, "internal error", f"Failed to initialize Twilio client: {str(e)}")

    def get_account_phone_numbers(self, account_name: str) -> Dict[str, Any]:
        """
        Get all phone numbers associated with the specified Twilio account.

        Args:
            account_name: Name of the Twilio account to query

        Returns:
            Dictionary containing raw response from Twilio API

        Raises:
            TwilioAPIException: If the query fails
        """
        client = self.get_client(account_name)

        try:
            # Fetch all phone numbers associated with the account
            phone_numbers = client.incoming_phone_numbers.list()

            return {
                "phone_numbers": [
                    {
                        # Basic Info
                        "sid": number.sid,
                        "phone_number": number.phone_number,
                        "friendly_name": number.friendly_name,
                        "account_sid": number.account_sid,
                        # Capabilities
                        "capabilities": number.capabilities,
                        # Configuration
                        "api_version": number.api_version,
                        "voice_url": number.voice_url,
                        "voice_method": number.voice_method,
                        "voice_fallback_url": number.voice_fallback_url,
                        "voice_fallback_method": number.voice_fallback_method,
                        "status_callback": number.status_callback,
                        "status_callback_method": number.status_callback_method,
                        "voice_caller_id_lookup": number.voice_caller_id_lookup,
                        # SMS Configuration
                        "sms_url": number.sms_url,
                        "sms_method": number.sms_method,
                        "sms_fallback_url": number.sms_fallback_url,
                        "sms_fallback_method": number.sms_fallback_method,
                        # Address Requirements
                        "address_requirements": number.address_requirements,
                        # Status and Dates
                        "status": number.status,
                        "date_created": str(number.date_created),
                        "date_updated": str(number.date_updated),
                        # Emergency Configuration
                        "emergency_status": number.emergency_status,
                        "emergency_address_sid": number.emergency_address_sid,
                        # Bundle Information
                        "bundle_sid": number.bundle_sid,
                        # Origin and Type
                        "origin": number.origin,
                        "trunk_sid": number.trunk_sid,
                        # Additional Properties
                        "identity_sid": number.identity_sid,
                        "address_sid": number.address_sid,
                    }
                    for number in phone_numbers
                ],
                "total": len(phone_numbers),
            }

        except TwilioRestException as e:
            logger.error(f"Twilio API error while fetching phone numbers: {str(e)}")
            raise TwilioAPIException(e.code, "twilio error", str(e))
        except Exception as e:
            logger.error(f"Error fetching phone numbers: {str(e)}")
            raise TwilioAPIException(500, "internal error", f"Failed to fetch phone numbers: {str(e)}")

    def send_message(
        self, account_name: str, to: str, body: str, from_: Optional[str] = None, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Send an SMS/MMS message using the specified Twilio account.

        Args:
            account_name: Name of the Twilio account to use
            to: Destination phone number (E.164 format)
            body: Message content
            from_: Optional sender phone number. If not provided, will use the first
                  available phone number from the account
            **kwargs: Additional parameters to pass to Twilio's create() method

        Returns:
            Dictionary containing the message details

        Raises:
            TwilioAPIException: If sending fails
        """
        client = self.get_client(account_name)

        try:
            # Import here to avoid circular import
            from ..models import TwilioAccount

            account = TwilioAccount.objects.get(name=account_name)
            if not from_:
                if not account.phone_numbers:
                    raise TwilioAPIException(
                        400, "bad request", f"No phone numbers configured for account '{account_name}'"
                    )
                from_ = account.phone_numbers[0]

            message = client.messages.create(to=to, from_=from_, body=body, **kwargs)

            return {
                "sid": message.sid,
                "status": message.status,
                "direction": message.direction,
                "from": message.from_,
                "to": message.to,
                "body": message.body,
                "date_created": message.date_created,
                "date_sent": message.date_sent,
                "price": message.price,
                "error_code": message.error_code,
                "error_message": message.error_message,
            }

        except TwilioRestException as e:
            logger.error(f"Twilio API error: {str(e)}")
            raise TwilioAPIException(e.code, "twilio error", str(e))
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            raise TwilioAPIException(500, "internal error", f"Failed to send message: {str(e)}")
