import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from projects.vault.services.vault_service import VaultService

from ..api.client import GoogleAdsApiClient

logger = logging.getLogger(__name__)


class ManagerAccount(models.Model):
    """
    Model for Ads Manager Accounts (MCC - My Client Center)
    """

    customer_id = models.CharField(max_length=12, unique=True, help_text="Manager Account ID (format: XXX-XXX-XXXX)")
    name = models.CharField(max_length=255, help_text="Account descriptive name")
    description = models.TextField(null=True, blank=True, help_text="Account description")
    currency_code = models.CharField(max_length=3, null=True, blank=True, help_text="Account currency code (e.g., USD)")
    time_zone = models.CharField(max_length=50, null=True, blank=True, help_text="Account timezone")
    vault_key = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Key used to store developer token in vault (e.g., manager_288244783)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        # Extract developer_token if provided in kwargs
        self._developer_token = kwargs.pop("developer_token", None)
        super().__init__(*args, **kwargs)
        self._vault_service = VaultService()

    @property
    def developer_token(self):
        """Get developer token from vault"""
        if not self.vault_key:
            return None

        secrets = self._vault_service.read_secret("dev", "google")
        if not secrets:
            return None

        return secrets.get(self.vault_key)

    @developer_token.setter
    def developer_token(self, value):
        """Temporarily store token to be saved to vault"""
        self._developer_token = value

    def verify_account_access(self):
        """Verify access to the manager account using the developer token"""
        if not self._developer_token:
            return

        try:
            # Create API client with this account's credentials
            client = GoogleAdsApiClient(
                customer_id=self.customer_id,
            )

            # Try to get account info - this will fail if we don't have access
            account_info = client.get_account_info()

            # Update account info from API if available
            if account_info:
                self.name = account_info.get("name", self.name)
                self.currency_code = account_info.get("currency", self.currency_code)
                self.time_zone = account_info.get("timezone", self.time_zone)

        except Exception as e:
            raise ValidationError(
                _(
                    "Could not verify access to this manager account. Please make sure you have logged "
                    "into this account in Google Ads and granted necessary permissions. Error: %(error)s"
                ),
                params={"error": str(e)},
            )

    def clean(self):
        # Validate customer_id format (XXX-XXX-XXXX)
        if not self.customer_id or not len(self.customer_id.replace("-", "")) == 10:
            raise ValidationError({"customer_id": _("Customer ID must be in format XXX-XXX-XXXX")})

        # Generate vault_key if not set and we have a developer token
        if not self.vault_key and self._developer_token:
            self.vault_key = f"manager_{self.customer_id.replace('-', '')}"

        # Verify account access if we have a developer token
        self.verify_account_access()

    def save(self, *args, **kwargs):
        self.full_clean()

        # If we have a new developer token, save it to vault
        if self._developer_token:
            env = "dev"  # You might want to make this configurable
            current_secrets = self._vault_service.read_secret(env, "google") or {}
            current_secrets[self.vault_key] = self._developer_token
            self._vault_service.write_secret(env, "google", current_secrets)
            self._developer_token = None  # Clear after saving

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.customer_id})"

    class Meta:
        verbose_name = "Manager Account"
        verbose_name_plural = "Manager Accounts"
        ordering = ["name"]
