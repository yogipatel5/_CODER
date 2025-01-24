# We are going to read the project name from project.yaml and use that to create or retrieve the vault.
# vault.py
import logging
import os

import hvac
import yaml
from dotenv import load_dotenv

load_dotenv()

vault_path = os.getenv("VAULT_ADDR")
vault_token = os.getenv("VAULT_TOKEN")


# The vault class will be used to import/export secrets into the vault


class Vault:
    def __init__(self, vault_path, vault_token):
        self.vault_path = vault_path
        self.vault_token = vault_token

    def create_secret_engine(self, project_name, environments):
        """
        Create a new KV version 2 secret engine for the project.

        Args:
            project_name (str): Name of the project to create the secret engine for
            environments (list): List of environments to create paths for (e.g., ['dev', 'prod'])

        Returns:
            dict: Dictionary of environment paths created
        """
        logging.info(f"Creating secret engine for project: {project_name} with environments: {environments}")

        # Initialize the Vault client
        client = hvac.Client(url=self.vault_path, token=self.vault_token)

        # Create a base path for the project
        base_path = f"{project_name}"
        env_paths = {}

        try:
            # Enable the KV version 2 secrets engine for the project
            try:
                client.sys.enable_secrets_engine(backend_type="kv", path=base_path, options={"version": "2"})
                logging.info(f"Created KV store at {base_path}")
            except hvac.exceptions.InvalidRequest as e:
                if "path is already in use" in str(e):
                    logging.info(f"KV store already exists at {base_path}")
                else:
                    raise

            # Create paths for each environment
            for env in environments:
                env_path = f"{base_path}/{env}"
                env_paths[env] = env_path

                try:
                    # Create a secret at the environment path to initialize it
                    client.secrets.kv.v2.create_or_update_secret(
                        path=env, secret={"initialized": True}, mount_point=base_path
                    )
                    logging.info(f"Initialized environment path: {env_path}")
                except Exception as e:
                    logging.error(f"Failed to initialize environment path {env_path}: {str(e)}")
                    raise

        except Exception as e:
            logging.error(f"Error creating secret engine: {str(e)}")
            return None

        return env_paths

    def list_secrets(self, path):
        """
        List all secrets in the vault for all environments.

        Args:
            path (str): Path to list secrets from

        Returns:
            dict: Dictionary of environments and their secrets
        """
        # Initialize the Vault client
        client = hvac.Client(url=self.vault_path, token=self.vault_token)

        logging.info("Listing secrets from vault")
        secrets_by_env = {}

        try:
            # List mounted secret engines
            mounted_secrets = client.sys.list_mounted_secrets_engines()
            if not isinstance(mounted_secrets, dict):
                logging.error(f"Unexpected response type from list_mounted_secrets_engines: {type(mounted_secrets)}")
                return {"error": "Invalid response from vault"}

            for mount_point, details in mounted_secrets.items():
                if not isinstance(details, dict):
                    continue

                if details.get("type") == "kv":  # Only look at KV secret engines
                    try:
                        # Remove trailing slash if present
                        mount_path = mount_point.rstrip("/")

                        # List secrets at this mount point
                        try:
                            list_response = client.secrets.kv.v2.list_secrets(path="", mount_point=mount_path)

                            if list_response and isinstance(list_response, dict) and "data" in list_response:
                                secrets = list_response["data"].get("keys", [])
                                secrets_by_env[mount_path] = secrets
                                logging.info(f"Found secrets in {mount_path}: {secrets}")
                            else:
                                logging.info(f"No secrets found in {mount_path} or newly created path")
                                secrets_by_env[mount_path] = []

                        except Exception as e:
                            if "404" in str(e):
                                logging.info(f"No secrets yet in newly created path {mount_path}")
                                secrets_by_env[mount_path] = []
                            else:
                                logging.warning(f"Error listing secrets for {mount_path}: {str(e)}")
                                secrets_by_env[mount_path] = []

                    except Exception as e:
                        logging.warning(f"Error processing mount point {mount_path}: {str(e)}")
                        secrets_by_env[mount_path] = []

        except Exception as e:
            logging.error(f"Error listing mounted secret engines: {str(e)}")
            return {"error": str(e)}

        return secrets_by_env

    def import_secret(self, secret_name, secret_value):
        # import the secret into the vault
        pass

    def export_secret(self, secret_name):
        # export the secret from the vault
        pass

    def delete_secret(self, secret_name):
        # delete the secret from the vault
        pass

    def update_secret(self, secret_name, secret_value):
        # update the secret in the vault
        pass

    def read_secret(self, secret_name):
        # read the secret from the vault
        pass


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    vault = Vault(vault_path, vault_token)

    # Use project.yaml to get projects_config
    with open("project.yaml", "r") as f:
        project_config = yaml.safe_load(f)

    # Get project name
    project_name = project_config.get("project_name")

    # Get environments from the vault configuration
    vault_config = project_config.get("env", {}).get("vault", [])
    environments = []
    for config in vault_config:
        if isinstance(config, dict) and "environments" in config:
            environments.extend([env["name"] for env in config["environments"]])

    # Create secret engine with project name and environments
    if project_name and environments:
        logging.info(f"Starting secret engine creation for project: {project_name}")
        env_paths = vault.create_secret_engine(project_name, environments)

        # Check if the secret engine was created successfully
        if env_paths:
            logging.info(f"Secret engine created successfully with paths: {env_paths}")
            # List secrets using the base project path
            secrets = vault.list_secrets(project_name)
            logging.info(f"Current secrets in vault: {secrets}")
        else:
            logging.error("Error: Could not create secret engine")
    else:
        logging.error("Error: Could not find project name or environments in project.yaml")
