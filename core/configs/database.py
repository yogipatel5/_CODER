"""Database configuration settings."""

import os

from core.secrets import secrets_manager

# Load secrets before configuring database
secrets_manager.load_secrets()

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DATABASE_NAME"),
        "USER": os.getenv("DATABASE_USER"),
        "PASSWORD": os.getenv("DATABASE_PASSWORD"),
        "HOST": os.getenv("DATABASE_HOST"),
        "PORT": os.getenv("DATABASE_PORT"),
        "CONN_MAX_AGE": int(os.getenv("DATABASE_CONN_MAX_AGE", "60")),  # 1 minute connection persistence
        "OPTIONS": {
            "connect_timeout": int(os.getenv("DATABASE_CONNECT_TIMEOUT", "10")),  # 10 seconds
        },
    }
}

# Cache using Redis
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": int(os.getenv("REDIS_CONNECT_TIMEOUT", "10")),  # 10 seconds
            "SOCKET_TIMEOUT": int(os.getenv("REDIS_SOCKET_TIMEOUT", "10")),  # 10 seconds
            "RETRY_ON_TIMEOUT": True,
        },
    }
}

# Use Redis for session cache
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
