from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from adwords.models.manager_model import ManagerAccount


class ClientAccount(models.Model):
    """
    Model for Ads Client Accounts
    """

    customer_id = models.CharField(max_length=12, unique=True, help_text="Client Account ID (format: XXX-XXX-XXXX)")
    manager = models.ForeignKey(
        ManagerAccount,
        on_delete=models.PROTECT,
        related_name="clients",
        help_text="Manager account that owns this client account",
    )
    name = models.CharField(max_length=255, help_text="Account descriptive name")
    currency_code = models.CharField(max_length=3, help_text="Account currency code (e.g., USD)")
    time_zone = models.CharField(max_length=50, help_text="Account timezone")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    # Additional fields specific to client accounts
    daily_budget = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, help_text="Daily budget in account currency"
    )
    website_url = models.URLField(max_length=255, null=True, blank=True, help_text="Primary website URL")
    business_name = models.CharField(
        max_length=255, null=True, blank=True, help_text="Business name associated with this account"
    )

    def clean(self):
        # Validate customer_id format (XXX-XXX-XXXX)
        if not self.customer_id or not len(self.customer_id.replace("-", "")) == 10:
            raise ValidationError({"customer_id": _("Customer ID must be in format XXX-XXX-XXXX")})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.customer_id})"

    class Meta:
        verbose_name = "Client Account"
        verbose_name_plural = "Client Accounts"
        ordering = ["name"]
