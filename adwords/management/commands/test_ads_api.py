import os

from django.core.management.base import BaseCommand

from adwords.api.client import GoogleAdsApiClient


class Command(BaseCommand):
    help = "Test Google Ads API authentication"

    def add_arguments(self, parser):
        parser.add_argument(
            "--get-token",
            action="store_true",
            help="Get a new refresh token",
        )

    def handle(self, *args, **options):
        # Get credentials from settings
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if not all([client_id, client_secret]):
            self.stdout.write(
                self.style.ERROR(
                    "Missing OAuth2 credentials. Please set GOOGLE_CLIENT_ID and "
                    "GOOGLE_CLIENT_SECRET in your environment."
                )
            )
            return

        # If --get-token flag is used, get a new refresh token
        if options["get_token"]:
            try:
                tokens = GoogleAdsApiClient.get_refresh_token(client_id, client_secret)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nSuccessfully obtained tokens!\n"
                        f"Refresh Token: {tokens['refresh_token']}\n"
                        f"Access Token: {tokens['access_token']}\n"
                        f"(Save the refresh token in your environment as GOOGLE_REFRESH_TOKEN)"
                    )
                )
                return
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error getting refresh token: {str(e)}"))
                return

        # Account credentials
        manager_id = "288-244-7837"  # Manager account
        client_id = "472-699-8842"  # Client account

        client = GoogleAdsApiClient(
            customer_id=client_id,
            manager_id=manager_id,
        )

        try:
            account_info = client.get_account_info()
            self.stdout.write(self.style.SUCCESS(f"Successfully retrieved account info: {account_info}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
