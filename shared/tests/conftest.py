"""Pytest configuration for shared app tests."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client


@pytest.fixture
def admin_user(db):
    """Create a superuser for admin tests."""
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="password123",
    )


@pytest.fixture
def admin_client(admin_user):
    """Create an authenticated admin client."""
    client = Client()
    client.force_login(admin_user)
    return client
