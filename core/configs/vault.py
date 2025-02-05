"""Vault configuration settings."""

import os

# Vault Configuration
VAULT_URL = os.getenv("VAULT_URL")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
VAULT_MOUNT_POINT = os.getenv("VAULT_MOUNT_POINT", "secret")
VAULT_PATH = os.getenv("VAULT_PATH", "django")
