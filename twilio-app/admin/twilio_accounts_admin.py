from django.contrib import admin
from django.utils.html import format_html
from twilio.models import TwilioAccount


@admin.register(TwilioAccount)
class TwilioAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "account_sid", "phone_numbers_display", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "account_sid")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        ("Account Information", {"fields": ("name", "account_sid", "vault_auth_token_path", "is_active")}),
        (
            "Phone Numbers",
            {
                "fields": ("phone_numbers",),
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def phone_numbers_display(self, obj):
        if not obj.phone_numbers:
            return "No phone numbers"
        phone_list = "<br>".join(obj.phone_numbers)
        return format_html(phone_list)

    phone_numbers_display.short_description = "Phone Numbers"

    def save_model(self, request, obj, form, change):
        obj.full_clean()  # Run model validation before saving
        super().save_model(request, obj, form, change)
