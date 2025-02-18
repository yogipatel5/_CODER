import logging
import os

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)


class GoogleAdsApiClient:
    def __init__(self, customer_id, manager_id=None):
        self.developer_token = os.getenv("GOOGLE_ADWORDS_DEVELOPER_TOKEN")
        # Remove dashes from customer IDs
        self.customer_id = customer_id.replace("-", "")
        self.manager_id = manager_id.replace("-", "") if manager_id else None
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")
        logger.debug(f"developer_token: {self.refresh_token}")
        self.client = self._create_client() if self.refresh_token else None

    def _create_client(self):
        credentials = {
            "developer_token": self.developer_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "use_proto_plus": True,
        }

        # Add login_customer_id if we're accessing through a manager account
        if self.manager_id:
            credentials["login_customer_id"] = self.manager_id

        return GoogleAdsClient.load_from_dict(credentials)

    @classmethod
    def get_refresh_token(cls, client_id, client_secret):
        """Get a refresh token using client credentials."""
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:63646"],
            }
        }

        SCOPES = ["https://www.googleapis.com/auth/adwords"]

        try:
            flow = InstalledAppFlow.from_client_config(client_config, scopes=SCOPES)

            # Use the specific port 63646
            credentials = flow.run_local_server(port=63646)

            return {"refresh_token": credentials.refresh_token, "access_token": credentials.token}

        except Exception as e:
            logger.error(f"Error getting refresh token: {str(e)}")
            raise

    def get_account_info(self):
        """Get basic account information."""
        if not self.client:
            raise ValueError("Client not initialized. Make sure you have a valid refresh token.")

        try:
            ga_service = self.client.get_service("GoogleAdsService")
            query = (
                """
                SELECT
                    customer.id,
                    customer.descriptive_name,
                    customer.currency_code,
                    customer.time_zone
                FROM customer
                WHERE customer.id = '%s'
            """
                % self.customer_id
            )

            response = ga_service.search(customer_id=self.customer_id, query=query)

            for row in response:
                return {
                    "id": row.customer.id,
                    "name": row.customer.descriptive_name,
                    "currency": row.customer.currency_code,
                    "timezone": row.customer.time_zone,
                }

        except GoogleAdsException as ex:
            logger.error(
                f"Request with ID '{ex.request_id}' failed with status "
                f"'{ex.error.code().name}' and includes the following errors:"
            )
            for error in ex.failure.errors:
                logger.error(f"\tError with message '{error.message}'.")
                if error.location:
                    for field_path_element in error.location.field_path_elements:
                        logger.error(f"\t\tOn field: {field_path_element.field_name}")
            raise
