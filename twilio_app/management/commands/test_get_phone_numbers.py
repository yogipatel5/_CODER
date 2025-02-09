import json

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from twilio_app.api.client import TwilioClientManager
from twilio_app.api.exceptions import TwilioAPIException


class Command(BaseCommand):
    help = "Test fetching phone numbers from a Twilio account"

    def add_arguments(self, parser):
        parser.add_argument("account_name", type=str, help="Name of the Twilio account to query")
        parser.add_argument("--raw", action="store_true", help="Show raw JSON response")

    def handle(self, *args, **options):
        account_name = options["account_name"]
        show_raw = options["raw"]

        try:
            client_manager = TwilioClientManager()
            result = client_manager.get_account_phone_numbers(account_name)

            if show_raw:
                self.stdout.write(json.dumps(result, indent=2))
                return

            self.stdout.write(
                self.style.SUCCESS(f"\nFound {result['total']} phone numbers for account '{account_name}':\n")
            )

            for number in result["phone_numbers"]:
                self.stdout.write(
                    f"Phone Number: {number['phone_number']}\n"
                    f"SID: {number['sid']}\n"
                    f"Friendly Name: {number['friendly_name']}\n"
                    f"Capabilities: {json.dumps(number['capabilities'], indent=2)}\n"
                    f"Status: {number['status']}\n"
                    f"Created: {number['date_created']}\n"
                    f"Updated: {number['date_updated']}\n"
                    f"Emergency Status: {number['emergency_status']}\n"
                    f"Voice URL: {number['voice_url']}\n"
                    f"SMS URL: {number['sms_url']}\n"
                    f"Origin: {number['origin']}\n"
                    f"{'-' * 50}\n"
                )

        except TwilioAPIException as e:
            self.stdout.write(self.style.ERROR(f"Twilio API Error: {e.message} (Code: {e.code})"))
        except ValidationError as e:
            self.stdout.write(self.style.ERROR(f"Validation Error: {str(e)}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected Error: {str(e)}"))
