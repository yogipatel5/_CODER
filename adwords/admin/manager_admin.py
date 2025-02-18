from django import forms
from django.contrib import admin

from adwords.models.manager_model import ManagerAccount


class ManagerAccountForm(forms.ModelForm):
    developer_token = forms.CharField(
        required=True, widget=forms.PasswordInput, help_text="Developer token will be stored in vault"
    )

    class Meta:
        model = ManagerAccount
        fields = [
            "customer_id",
            "name",
            "description",
            "currency_code",
            "time_zone",
            "is_active",
            "developer_token",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["developer_token"].help_text += " (Leave empty to keep current token)"


@admin.register(ManagerAccount)
class ManagerAccountAdmin(admin.ModelAdmin):
    form = ManagerAccountForm
    list_display = [
        "customer_id",
        "name",
        "description",
        "currency_code",
        "time_zone",
        "is_active",
        "has_developer_token",
    ]
    list_filter = ["is_active", "currency_code"]
    search_fields = ["customer_id", "name"]
    readonly_fields = ["vault_key"]

    def has_developer_token(self, obj):
        """Check if account has a developer token in vault"""
        return bool(obj.developer_token)

    has_developer_token.boolean = True
    has_developer_token.short_description = "Has Token"

    def save_model(self, request, obj, form, change):
        """Save the model and handle developer token"""
        if form.cleaned_data.get("developer_token"):
            obj.developer_token = form.cleaned_data["developer_token"]
        obj.save()
