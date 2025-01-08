"""Nginx proxy Django app configuration."""

from django.apps import AppConfig


class NginxProxyConfig(AppConfig):
    """Nginx proxy app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "network.nginxproxy"
