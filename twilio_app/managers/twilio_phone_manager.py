from typing import Any, Dict, Optional, Tuple

from django.db import models
from django.utils.timezone import datetime


class TwilioPhoneManager(models.Manager):
    """Manager for TwilioPhoneNumber model"""

    def create_or_update_from_twilio(
        self, account: "TwilioAccount", data: Dict[str, Any]
    ) -> Tuple["TwilioPhoneNumber", bool]:
        """
        Create or update a TwilioPhoneNumber instance from Twilio API data

        Args:
            account: TwilioAccount instance
            data: Dictionary containing Twilio API response for a phone number

        Returns:
            Tuple of (TwilioPhoneNumber instance, bool indicating if created)
        """
        capabilities = data.get("capabilities", {})

        # Parse datetime strings
        date_created = datetime.fromisoformat(data["date_created"].replace("Z", "+00:00"))
        date_updated = datetime.fromisoformat(data["date_updated"].replace("Z", "+00:00"))

        defaults = {
            "phone_number": data["phone_number"],
            "friendly_name": data["friendly_name"],
            "account": account,
            # Capabilities
            "capability_voice": capabilities.get("voice", False),
            "capability_sms": capabilities.get("sms", False),
            "capability_mms": capabilities.get("mms", False),
            "capability_fax": capabilities.get("fax", False),
            # Configuration
            "api_version": data["api_version"],
            "voice_url": data["voice_url"] or "",
            "voice_method": data["voice_method"],
            "voice_fallback_url": data["voice_fallback_url"],
            "voice_fallback_method": data["voice_fallback_method"],
            "status_callback": data["status_callback"],
            "status_callback_method": data["status_callback_method"],
            "voice_caller_id_lookup": data["voice_caller_id_lookup"],
            # SMS Configuration
            "sms_url": data["sms_url"] or "",
            "sms_method": data["sms_method"],
            "sms_fallback_url": data["sms_fallback_url"],
            "sms_fallback_method": data["sms_fallback_method"],
            # Address and Emergency
            "address_requirements": data["address_requirements"],
            "emergency_status": data["emergency_status"],
            "emergency_address_sid": data["emergency_address_sid"],
            "address_sid": data["address_sid"],
            # Additional Properties
            "bundle_sid": data["bundle_sid"],
            "identity_sid": data["identity_sid"],
            "trunk_sid": data["trunk_sid"],
            "origin": data["origin"],
            # Status and Timestamps
            "status": data["status"],
            "date_created": date_created,
            "date_updated": date_updated,
        }

        return self.update_or_create(sid=data["sid"], defaults=defaults)
