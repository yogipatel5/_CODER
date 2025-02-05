"""Django settings for core project."""

import logging
import os
from pathlib import Path

import yaml

from core.configs import celery, database, jazzmin, security, vault
from core.configs.logging import LOGGING
from core.secrets import secrets_manager

# Load all secrets and set environment variables
secrets_manager.load_secrets()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Debug logging for Redis and Celery configuration
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.debug("Redis Configuration:")
logger.debug(f"REDIS_HOST: {os.getenv('REDIS_HOST')}")
logger.debug(f"REDIS_PORT: {os.getenv('REDIS_PORT')}")
logger.debug("\nCelery Configuration:")
logger.debug(f"CELERY_BROKER_URL: {os.getenv('CELERY_BROKER_URL')}")
logger.debug(f"CELERY_RESULT_BACKEND: {os.getenv('CELERY_RESULT_BACKEND')}")

# if project.yaml exists, load it
try:
    with open("project.yaml", "r") as f:
        project_config = yaml.safe_load(f)

    # Set environment variables from project.yaml
    for key, value in project_config.get("env", {}).items():
        os.environ[key] = str(value)

except FileNotFoundError:
    pass

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Import all settings from config modules
vars().update(celery.__dict__)
vars().update(database.__dict__)
vars().update(jazzmin.__dict__)
vars().update(LOGGING)
vars().update(security.__dict__)
vars().update(vault.__dict__)

# Application definition
INSTALLED_APPS = [
    "shared",
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "alfie.apps.AlfieConfig",
    "core.apps.CoreConfig",
    "projects.djhelper.apps.DJHelperAppConfig",
    "notifier.apps.NotifierConfig",
    "projects.vault.apps.VaultConfig",
    "notion.apps.NotionConfig",
    "pfsense.apps.PfsenseConfig",
    "system.apps.SystemConfig",
    "network.proxmox.apps.ProxmoxConfig",
    "print.apps.PrintConfig",
    "django_celery_beat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE")
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
