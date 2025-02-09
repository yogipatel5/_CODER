from django.contrib import admin
from django.utils.html import format_html

from ..models import TwilioPhoneNumber


@admin.register(TwilioPhoneNumber)
class TwilioPhoneNumberAdmin(admin.ModelAdmin):
    list_display = [
        "phone_number",
        "friendly_name",
        "account",
        "status",
        "capabilities_display",
        "emergency_status",
        "date_created",
        "date_updated",
    ]

    list_filter = [
        "account",
        "status",
        "emergency_status",
        "capability_voice",
        "capability_sms",
        "capability_mms",
        "capability_fax",
    ]

    search_fields = [
        "phone_number",
        "friendly_name",
        "sid",
        "account__name",
    ]

    readonly_fields = [
        "sid",
        "phone_number",
        "friendly_name",
        "account",
        "api_version",
        "capability_voice",
        "capability_sms",
        "capability_mms",
        "capability_fax",
        "voice_url",
        "voice_method",
        "voice_fallback_url",
        "voice_fallback_method",
        "status_callback",
        "status_callback_method",
        "voice_caller_id_lookup",
        "sms_url",
        "sms_method",
        "sms_fallback_url",
        "sms_fallback_method",
        "address_requirements",
        "emergency_status",
        "emergency_address_sid",
        "address_sid",
        "bundle_sid",
        "identity_sid",
        "trunk_sid",
        "origin",
        "status",
        "date_created",
        "date_updated",
    ]

    fieldsets = [
        (
            "Basic Information",
            {
                "fields": [
                    "sid",
                    "phone_number",
                    "friendly_name",
                    "account",
                    "status",
                    "origin",
                ]
            },
        ),
        (
            "Capabilities",
            {
                "fields": [
                    "capability_voice",
                    "capability_sms",
                    "capability_mms",
                    "capability_fax",
                ]
            },
        ),
        (
            "Voice Configuration",
            {
                "fields": [
                    "voice_url",
                    "voice_method",
                    "voice_fallback_url",
                    "voice_fallback_method",
                    "status_callback",
                    "status_callback_method",
                    "voice_caller_id_lookup",
                ]
            },
        ),
        (
            "SMS Configuration",
            {
                "fields": [
                    "sms_url",
                    "sms_method",
                    "sms_fallback_url",
                    "sms_fallback_method",
                ]
            },
        ),
        (
            "Emergency & Address",
            {
                "fields": [
                    "emergency_status",
                    "emergency_address_sid",
                    "address_requirements",
                    "address_sid",
                ]
            },
        ),
        (
            "Additional Information",
            {
                "fields": [
                    "api_version",
                    "bundle_sid",
                    "identity_sid",
                    "trunk_sid",
                    "date_created",
                    "date_updated",
                ]
            },
        ),
    ]

    def capabilities_display(self, obj):
        """Display capabilities as colored badges"""
        badges = []
        if obj.capability_voice:
            badges.append(
                '<span style="background-color: #28a745; color: white; padding: 2px 6px; border-radius: 3px;">Voice</span>'
            )
        if obj.capability_sms:
            badges.append(
                '<span style="background-color: #007bff; color: white; padding: 2px 6px; border-radius: 3px;">SMS</span>'
            )
        if obj.capability_mms:
            badges.append(
                '<span style="background-color: #17a2b8; color: white; padding: 2px 6px; border-radius: 3px;">MMS</span>'
            )
        if obj.capability_fax:
            badges.append(
                '<span style="background-color: #6c757d; color: white; padding: 2px 6px; border-radius: 3px;">Fax</span>'
            )

        return format_html("&nbsp;".join(badges))

    capabilities_display.short_description = "Capabilities"

    def has_add_permission(self, request):
        """Disable manual creation of phone numbers"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deletion of phone numbers from admin"""
        return False
