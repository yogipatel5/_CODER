"""
Configure pytest for Django testing.
"""

import os

import django
import pytest


def pytest_configure():
    """Configure Django for testing."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    django.setup()


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Enable database access for all tests.
    This is equivalent to using the pytest.mark.django_db decorator on all test functions.
    """
    pass  # pragma: no cover
