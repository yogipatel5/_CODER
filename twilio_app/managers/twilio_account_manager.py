from typing import TYPE_CHECKING  # noqa

if TYPE_CHECKING:
    from twilio_app.models import TwilioAccount, TwilioPhoneNumber

from django.db import models

from ..api.client import TwilioClientManager


class TwilioAccountManager(models.Manager):
    """Manager for TwilioAccount model"""

    def get_by_name(self, name: str, active_only: bool = True) -> "TwilioAccount":
        """
        Get a Twilio account by name

        Args:
            name: Name of the account to get
            active_only: Only return active accounts

        Returns:
            TwilioAccount instance

        Raises:
            TwilioAccount.DoesNotExist: If account not found
        """
        qs = self.get_queryset()
        if active_only:
            qs = qs.filter(is_active=True)
        return qs.get(name=name)

    def sync_phone_numbers(self, account: "TwilioAccount") -> None:
        """
        Sync phone numbers from Twilio API to local database

        Args:
            account: TwilioAccount instance to sync numbers for

        Raises:
            TwilioAPIException: If there's an error fetching phone numbers
        """

        client_manager = TwilioClientManager()
        result = client_manager.get_account_phone_numbers(account.name)

        phone_manager = TwilioPhoneNumber.objects
        for phone_data in result["phone_numbers"]:
            phone_manager.create_or_update_from_twilio(account, phone_data)
