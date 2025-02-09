from django.contrib import admin
from django.utils.html import format_html

from twilio_app.models import TwilioAccount


@admin.register(TwilioAccount)
class TwilioAccountAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "account_sid",
        "is_active",
        "phone_numbers_count",
        "created_at",
        "updated_at",
    ]

    list_filter = ["is_active"]
    search_fields = ["name", "account_sid"]
    readonly_fields = ["created_at", "updated_at", "phone_numbers_count"]

    fieldsets = [
        (
            "Account Information",
            {
                "fields": [
                    "name",
                    "account_sid",
                    "vault_auth_token_path",
                    "is_active",
                ]
            },
        ),
        (
            "Phone Numbers",
            {
                "fields": ["phone_numbers_count"],
                "description": "Phone numbers are automatically synced from Twilio when the account is created.",
            },
        ),
        ("Timestamps", {"fields": ["created_at", "updated_at"]}),
    ]

    def phone_numbers_count(self, obj):
        """Display count of associated phone numbers with a link to filtered phone numbers view"""
        count = obj.phone_numbers.count()
        if count > 0:
            url = f"/admin/twilio_app/twiliophone/?account__id__exact={obj.id}"
            return format_html('<a href="{}">{} phone numbers</a>', url, count)
        return "0 phone numbers"

    phone_numbers_count.short_description = "Phone Numbers"

    def save_model(self, request, obj, form, change):
        """Override save_model to sync phone numbers if this is a new account"""
        is_new = not obj.pk
        super().save_model(request, obj, form, change)

        if is_new:
            obj.sync_phone_numbers()
