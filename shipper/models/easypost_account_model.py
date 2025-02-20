import logging

from django.db import models

from ..managers import EasyPostAccountManager

logger = logging.getLogger(__name__)


class EasyPostAccountModel(models.Model):
    account_name = models.CharField(max_length=255, unique=True, help_text="Unique name for the EasyPost account")
    email = models.EmailField(help_text="Email associated with the EasyPost account")
    api_key_name = models.CharField(
        max_length=255, unique=True, help_text="Name used to store/retrieve API key from vault"
    )
    vault_path = models.CharField(
        max_length=512, blank=True, help_text="Full path where the API key is stored in vault"
    )
    test_api_key_name = models.CharField(
        max_length=255, blank=True, unique=True, help_text="Name used to store/retrieve test API key from vault"
    )
    test_vault_path = models.CharField(
        max_length=512, blank=True, help_text="Full path where the test API key is stored in vault"
    )
    account_id = models.CharField(max_length=255, blank=True, help_text="EasyPost account ID retrieved from API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False, help_text="Whether this is the default EasyPost account")

    objects = EasyPostAccountManager()

    class Meta:
        verbose_name = "EasyPost Account"
        verbose_name_plural = "EasyPost Accounts"

    def __str__(self):
        return f"{self.account_name} ({self.email})"

    def clean(self):
        if not self.api_key_name:
            self.api_key_name = f"EASYPOST_API_KEY_{self.account_name.upper().replace(' ', '_')}"
        if not self.test_api_key_name and hasattr(self, "_temp_test_api_key"):
            self.test_api_key_name = f"EASYPOST_TEST_API_KEY_{self.account_name.upper().replace(' ', '_')}"

    def save(self, *args, **kwargs):
        self.clean()
        if self.is_default:
            # Set all other accounts' is_default to False
            type(self).objects.exclude(pk=self.pk).update(is_default=False)
        elif not self.pk and not type(self).objects.exists():
            # If this is the first account being created, make it default
            self.is_default = True
        if not self.pk:  # Only validate on creation
            type(self).objects.validate_and_store_api_key(self)
        super().save(*args, **kwargs)
