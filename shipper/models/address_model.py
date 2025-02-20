import logging

from django.db import models

logger = logging.getLogger(__name__)


class AddressModel(models.Model):
    name = models.CharField(max_length=255, help_text="Name for this address")
    company = models.CharField(max_length=255, blank=True, help_text="Company name")
    street1 = models.CharField(max_length=255, help_text="Street address line 1")
    street2 = models.CharField(max_length=255, blank=True, help_text="Street address line 2")
    city = models.CharField(max_length=255, help_text="City")
    state = models.CharField(max_length=2, help_text="State (2-letter code)")
    zip_code = models.CharField(max_length=10, help_text="ZIP code")
    country = models.CharField(max_length=2, default="US", help_text="Country code (2-letter)")
    phone = models.CharField(max_length=20, blank=True, help_text="Phone number")
    email = models.EmailField(blank=True, help_text="Email address")

    # Optional relationship to EasyPost account if this is a default ship-from address
    default_ship_from_for = models.ForeignKey(
        "shipper.EasyPostAccountModel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="default_ship_from_address",
        help_text="EasyPost account that uses this as default ship-from address",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["zip_code"]),
        ]

    def __str__(self):
        parts = [self.name]
        if self.company:
            parts.append(f"({self.company})")
        parts.append(f"{self.city}, {self.state} {self.zip_code}")
        return " ".join(parts)

    def to_easypost_dict(self):
        """Convert to dict format expected by EasyPost API"""
        return {
            "name": self.name,
            "company": self.company,
            "street1": self.street1,
            "street2": self.street2,
            "city": self.city,
            "state": self.state,
            "zip": self.zip_code,
            "country": self.country,
            "phone": self.phone,
            "email": self.email,
        }
