from django.core.exceptions import ValidationError
from django.db import models

from twilio_app.managers import TwilioPhoneManager


class TwilioPhoneNumber(models.Model):
    """Model for storing Twilio phone number information"""

    # Basic Info
    sid = models.CharField(max_length=34, unique=True, help_text="Twilio Phone Number SID")
    phone_number = models.CharField(max_length=20, help_text="Phone number in E.164 format")
    friendly_name = models.CharField(max_length=100, help_text="Friendly name for the phone number")
    account = models.ForeignKey(
        "TwilioAccount", on_delete=models.CASCADE, related_name="phone_numbers", help_text="Associated Twilio account"
    )

    # Capabilities
    capability_voice = models.BooleanField(default=False)
    capability_sms = models.BooleanField(default=False)
    capability_mms = models.BooleanField(default=False)
    capability_fax = models.BooleanField(default=False)

    # Configuration
    api_version = models.CharField(max_length=20, help_text="Twilio API version")
    voice_url = models.URLField(max_length=255, null=True, blank=True)
    voice_method = models.CharField(max_length=10, default="POST")
    voice_fallback_url = models.URLField(max_length=255, null=True, blank=True)
    voice_fallback_method = models.CharField(max_length=10, default="POST")
    status_callback = models.URLField(max_length=255, null=True, blank=True)
    status_callback_method = models.CharField(max_length=10, default="POST")
    voice_caller_id_lookup = models.BooleanField(default=False)

    # SMS Configuration
    sms_url = models.URLField(max_length=255, null=True, blank=True)
    sms_method = models.CharField(max_length=10, default="POST")
    sms_fallback_url = models.URLField(max_length=255, null=True, blank=True)
    sms_fallback_method = models.CharField(max_length=10, default="POST")

    # Address and Emergency
    address_requirements = models.CharField(max_length=20, default="none")
    emergency_status = models.CharField(max_length=20)
    emergency_address_sid = models.CharField(max_length=34, null=True, blank=True)
    address_sid = models.CharField(max_length=34, null=True, blank=True)

    # Additional Properties
    bundle_sid = models.CharField(max_length=34, null=True, blank=True)
    identity_sid = models.CharField(max_length=34, null=True, blank=True)
    trunk_sid = models.CharField(max_length=34, null=True, blank=True)
    origin = models.CharField(max_length=50)

    # Status and Timestamps
    status = models.CharField(max_length=20)
    date_created = models.DateTimeField()
    date_updated = models.DateTimeField()

    objects = TwilioPhoneManager()

    class Meta:
        verbose_name = "Twilio Phone Number"
        verbose_name_plural = "Twilio Phone Numbers"
        ordering = ["phone_number"]
        indexes = [
            models.Index(fields=["phone_number"]),
            models.Index(fields=["account", "status"]),
        ]

    def __str__(self):
        return f"{self.friendly_name} ({self.phone_number})"

    def clean(self):
        # Validate phone number format (E.164)
        if not self.phone_number.startswith("+") or not self.phone_number[1:].isdigit():
            raise ValidationError({"phone_number": "Phone number must be in E.164 format (e.g., +17622388677)"})

        # Validate SID format
        if not self.sid.startswith("PN") or len(self.sid) != 34:
            raise ValidationError({"sid": 'SID must start with "PN" and be 34 characters long'})
