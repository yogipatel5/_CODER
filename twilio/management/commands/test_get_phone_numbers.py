from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from twilio_app.api.client import TwilioClientManager
from twilio_app.api.exceptions import TwilioAPIException


class Command(BaseCommand):
    help = "Test fetching phone numbers from a Twilio account"

    def add_arguments(self, parser):
        parser.add_argument("account_name", type=str, help="Name of the Twilio account to query")

    def handle(self, *args, **options):
        account_name = options["account_name"]

        try:
            client_manager = TwilioClientManager()
            result = client_manager.get_account_phone_numbers(account_name)

            self.stdout.write(
                self.style.SUCCESS(f"\nFound {result['total']} phone numbers for account '{account_name}':\n")
            )

            for number in result["phone_numbers"]:
                self.stdout.write(
                    f"Phone Number: {number['phone_number']}\n"
                    f"Friendly Name: {number['friendly_name']}\n"
                    f"SID: {number['sid']}\n"
                    f"Capabilities: SMS={number['capabilities']['sms']}, "
                    f"MMS={number['capabilities']['mms']}, "
                    f"Voice={number['capabilities']['voice']}\n"
                    f"Status: {number['status']}\n"
                    f"{'-' * 50}\n"
                )

        except TwilioAPIException as e:
            self.stdout.write(self.style.ERROR(f"Twilio API Error: {e.message} (Code: {e.code})"))
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f"Validation Error: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected Error: {str(e)}"))
