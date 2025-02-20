from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from ..api.easypost_client import EasyPostClient
from ..models import AddressModel, EasyPostAccountModel


class EasyPostAccountForm(forms.ModelForm):
    api_key = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Enter the EasyPost API key. This will be validated and stored securely.",
        required=False,  # Make it not required by default
    )
    test_api_key = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Optional: Enter the EasyPost test API key. This will be validated and stored securely.",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # If creating new account
            self.fields["api_key"].required = True  # Make API key required only for new accounts
            self.fields["api_key"].help_text = "Enter the EasyPost API key. Required for new accounts."

    class Meta:
        model = EasyPostAccountModel
        fields = ["account_name", "email", "api_key", "test_api_key", "is_active", "is_default"]

    def clean(self):
        cleaned_data = super().clean()
        # If editing and neither key is provided, return early
        if self.instance.pk and not (cleaned_data.get("api_key") or cleaned_data.get("test_api_key")):
            return cleaned_data
        return cleaned_data

    def clean_api_key(self):
        """Validate the API key before proceeding"""
        api_key = self.cleaned_data.get("api_key")

        # Skip validation if no API key provided during edit
        if not api_key:
            return api_key

        is_valid, result = EasyPostClient.validate_api_key(api_key)
        if not is_valid:
            raise ValidationError(f"Invalid API key: {result}")

        # Store the validated API key temporarily
        self.instance._temp_api_key = api_key
        return api_key

    def clean_test_api_key(self):
        """Validate the test API key if provided"""
        test_api_key = self.cleaned_data.get("test_api_key")

        if not test_api_key:
            return test_api_key

        is_valid, result = EasyPostClient.validate_api_key(test_api_key, is_test=True)
        if not is_valid:
            raise ValidationError(f"Invalid test API key: {result}")

        # Store the validated test API key temporarily
        self.instance._temp_test_api_key = test_api_key
        return test_api_key


@admin.register(EasyPostAccountModel)
class EasyPostAccountAdmin(admin.ModelAdmin):
    form = EasyPostAccountForm
    list_display = ["account_name", "email", "account_id", "is_active", "is_default", "created_at", "updated_at"]
    list_filter = ["is_active", "is_default", "created_at", "updated_at"]
    search_fields = ["account_name", "email", "account_id"]
    readonly_fields = [
        "account_id",
        "api_key_name",
        "vault_path",
        "test_api_key_name",
        "test_vault_path",
        "created_at",
        "updated_at",
    ]

    def get_readonly_fields(self, request, obj=None):
        """Make more fields readonly when editing an existing object"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ["account_name", "email"]
        return self.readonly_fields

    def save_model(self, request, obj, form, change):
        """Custom save method to handle API key validation and storage"""
        if not change:  # Only for new objects
            # API key validation already done in form.clean_api_key
            # save() will handle storing in vault via the manager
            super().save_model(request, obj, form, change)
        else:
            # For existing objects, just save the changes
            super().save_model(request, obj, form, change)


@admin.register(AddressModel)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "city", "state", "zip_code", "default_ship_from_for", "is_active"]
    list_filter = ["is_active", "state", "country"]
    search_fields = ["name", "company", "street1", "street2", "city", "zip_code"]
    fieldsets = [
        (None, {"fields": ["name", "company", "is_active"]}),
        ("Address Details", {"fields": ["street1", "street2", "city", "state", "zip_code", "country"]}),
        ("Contact Information", {"fields": ["phone", "email"]}),
        (
            "EasyPost Settings",
            {
                "fields": ["default_ship_from_for"],
                "description": "Optional: Set this address as the default ship-from address for an EasyPost account",
            },
        ),
    ]

    def save_model(self, request, obj, form, change):
        """Ensure only one address is default for each EasyPost account"""
        if obj.default_ship_from_for:
            # Clear any other default addresses for this EasyPost account
            AddressModel.objects.filter(default_ship_from_for=obj.default_ship_from_for).exclude(pk=obj.pk).update(
                default_ship_from_for=None
            )
        super().save_model(request, obj, form, change)
