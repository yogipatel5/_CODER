from django.core.management.base import BaseCommand

from twilio_app.api.exceptions import TwilioAPIException
from twilio_app.models import TwilioAccount


class Command(BaseCommand):
    help = "Create or update the YPGOC Twilio account and sync its phone numbers"

    def handle(self, *args, **options):
        account_name = "YPGOC"
        vault_path = "TWILIO_YP"  # Will look for TWILIO_YP_AUTH_TOKEN in env

        # Create or update the account
        account, created = TwilioAccount.objects.update_or_create(
            name=account_name,
            defaults={
                "vault_auth_token_path": vault_path,
                "is_active": True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created new Twilio account: {account}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Updated existing Twilio account: {account}"))

        # Sync phone numbers
        try:
            TwilioAccount.objects.sync_phone_numbers(account)
            self.stdout.write(self.style.SUCCESS("Successfully synced phone numbers"))

            # Show the synced numbers
            numbers = account.phone_numbers.all()
            self.stdout.write("\nSynced phone numbers:")
            for number in numbers:
                self.stdout.write(f"- {number.friendly_name} ({number.phone_number})")
        except TwilioAPIException as e:
            self.stdout.write(self.style.ERROR(f"Failed to sync phone numbers: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error syncing phone numbers: {str(e)}"))
