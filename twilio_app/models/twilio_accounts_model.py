from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from ..managers.twilio_account_manager import TwilioAccountManager


class TwilioAccount(models.Model):
    """Model for storing Twilio account information"""

    name = models.CharField(max_length=100, help_text="Friendly name for the Twilio account")
    account_sid = models.CharField(max_length=34, unique=True, help_text="Twilio Account SID")
    vault_auth_token_path = models.CharField(max_length=255, help_text="Path in vault where the auth token is stored")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TwilioAccountManager()

    class Meta:
        verbose_name = "Twilio Account"
        verbose_name_plural = "Twilio Accounts"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.account_sid})"

    def clean(self):
        # Validate account_sid format (starts with 'AC' and is 34 chars long)
        if not self.account_sid.startswith("AC") or len(self.account_sid) != 34:
            raise ValidationError({"account_sid": 'Account SID must start with "AC" and be 34 characters long'})


@receiver(post_save, sender=TwilioAccount)
def sync_phone_numbers_on_create(sender, instance, created, **kwargs):
    """
    Signal handler to sync phone numbers when a new account is created
    """
    if created:
        TwilioAccount.objects.sync_phone_numbers(instance)
