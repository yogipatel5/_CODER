"""Test task lifecycle management."""

from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from shared.celery.task import shared_task
from shared.models import SharedTask
from shared.utils.time import format_next_run, format_timedelta


# Test task model
class TestTask(SharedTask):
    """Test task model."""

    class Meta:
        app_label = "shared"


# Test task function
@shared_task(name="shared.tasks.test_task")
def test_task(succeed=True):
    """Test task that can succeed or fail."""
    if not succeed:
        raise ValueError("Task failed as requested")
    return {"count": 42, "status": "success"}


@pytest.fixture
def task_config():
    """Create a test task configuration."""
    return TestTask.objects.create(
        name="shared.tasks.test_task",
        description="Test task",
        is_active=True,
        notify_on_error=True,
        disable_on_error=True,
    )


@pytest.mark.django_db
class TestTaskLifecycle:
    """Test task lifecycle management."""

    def test_task_success(self, task_config):
        """Test successful task execution."""
        # Run task
        result = test_task()

        # Verify task state
        task_config.refresh_from_db()
        assert task_config.last_status == "success"
        assert task_config.last_result == {"count": 42, "status": "success"}
        assert task_config.last_error == ""
        assert task_config.is_active is True
        assert task_config.last_run is not None

    def test_task_error(self, task_config):
        """Test task error handling."""
        # Mock notification service
        with patch("notifier.services.notify_me.NotifyMeTask.notify_me") as mock_notify:
            # Run task with error
            with pytest.raises(ValueError):
                test_task(succeed=False)

            # Verify task state
            task_config.refresh_from_db()
            assert task_config.last_status == "error"
            assert "Task failed as requested" in task_config.last_error
            assert task_config.is_active is False  # Disabled due to error
            assert task_config.last_run is not None

            # Verify notification was sent
            mock_notify.assert_called_once()
            assert "Task Error" in mock_notify.call_args[1]["title"]

    def test_inactive_task(self, task_config):
        """Test that inactive tasks are skipped."""
        # Disable task
        task_config.is_active = False
        task_config.save()

        # Run task
        result = test_task()

        # Verify task wasn't tracked
        task_config.refresh_from_db()
        assert task_config.last_run is None
        assert task_config.last_status is None

    def test_time_formatting(self):
        """Test time formatting utilities."""
        now = timezone.now()

        # Test timedelta formatting
        delta = timezone.timedelta(hours=2, minutes=30)
        assert format_timedelta(delta) == "2hr 30m"

        # Test next run formatting
        next_run = now + timezone.timedelta(hours=1)
        assert "in 1h" in format_next_run(next_run)


@pytest.mark.django_db
class TestTaskAdmin:
    """Test task admin functionality."""

    def test_error_count_display(self, task_config, admin_client):
        """Test error count display in admin."""
        # Create some errors
        task_config.errors.create(
            error_type="ValueError",
            error_message="Test error",
            function_name="test_func",
        )

        # Get admin page
        response = admin_client.get(f"/admin/shared/task/{task_config.id}/change/")
        assert response.status_code == 200

        # Verify error count is shown
        content = response.content.decode()
        assert "1" in content  # Error count should be visible
