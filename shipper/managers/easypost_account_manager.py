import json
import logging

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import models

from projects.vault.services.vault_service import VaultService

from ..api.easypost_client import EasyPostClient

logger = logging.getLogger(__name__)


class EasyPostAccountManager(models.Manager):
    def validate_and_store_api_key(self, instance):
        """
        Validates the API key by making a test API call and stores it in vault.
        The API key should be passed through the instance before saving.
        """
        api_key = getattr(instance, "_temp_api_key", None)
        if not api_key:
            raise ValidationError("API key is required for new accounts")

        try:
            # Validate the API key
            is_valid, result = EasyPostClient.validate_api_key(api_key)
            if not is_valid:
                raise ValidationError(f"Invalid API key: {result}")

            instance.account_id = result

            # Store in vault using management command
            env = "dev"  # We're always using prod for EasyPost keys

            # Call the management command to store the secret
            call_command(
                "create_update_secret",
                env=env,
                name="easypost",
                value=json.dumps({instance.api_key_name: api_key}),
                verbosity=0,
            )

            # Set the vault path
            vault_service = VaultService()
            instance.vault_path = f"{vault_service.mount_point}/{env}/easypost/{instance.api_key_name}"
            logger.info(f"Successfully stored API key for {instance.account_name}")

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error storing API key: {str(e)}")
            raise ValidationError(f"Error storing API key: {str(e)}")
        finally:
            # Clear the temporary API key
            delattr(instance, "_temp_api_key")

    def get_api_key(self, instance) -> str:
        """
        Retrieves the API key from vault using the stored vault path.
        """
        if not instance.vault_path:
            raise ValidationError("No vault path stored for this account")

        try:
            # Split vault path into components
            parts = instance.vault_path.split("/")
            if len(parts) < 4:  # We now expect mount/env/easypost/key_name
                raise ValidationError(f"Invalid vault path: {instance.vault_path}")

            env = parts[-3]  # Third to last part is the environment
            name = "easypost"  # We store all keys under 'easypost'
            key_name = parts[-1]  # Last part is the specific key name

            vault_service = VaultService()
            secret = vault_service.read_secret(env=env, name=name)

            if not secret or key_name not in secret:
                raise ValidationError("API key not found in vault")

            return secret[key_name]

        except Exception as e:
            logger.error(f"Error retrieving API key from vault: {str(e)}")
            raise ValidationError(f"Error retrieving API key: {str(e)}")
