"""Manager for task scheduling functionality."""

import logging
from typing import Optional

from django.utils import timezone

from .base_task_manager import BaseTaskManager

logger = logging.getLogger(__name__)


class TaskScheduleManager(BaseTaskManager):
    """Manager for task scheduling functionality."""

    def _get_last_run(self, task) -> Optional[timezone.datetime]:
        """Get the timezone-aware last run time from the periodic task."""
        # Use the last_run from periodic_task as it's more accurate
        if not task.periodic_task or not task.periodic_task.last_run_at:
            return None

        last_run = task.periodic_task.last_run_at
        if timezone.is_naive(last_run):
            last_run = timezone.make_aware(last_run)

        return last_run

    def _calculate_next_run_for_interval(self, task, last_run: timezone.datetime) -> timezone.datetime:
        """Calculate the next run time for an interval schedule."""
        interval = task.periodic_task.interval

        # Convert the interval to timedelta
        if interval.period == "days":
            td = timezone.timedelta(days=interval.every)
        elif interval.period == "hours":
            td = timezone.timedelta(hours=interval.every)
        elif interval.period == "minutes":
            td = timezone.timedelta(minutes=interval.every)
        elif interval.period == "seconds":
            td = timezone.timedelta(seconds=interval.every)
        else:
            # Default to hourly if unknown period
            td = timezone.timedelta(hours=1)

        # Calculate next run time
        next_run = last_run + td
        now = timezone.now()

        # If next run is in the past, calculate the next occurrence from now
        if next_run < now:
            # Calculate how many intervals have passed
            time_since_last = now - last_run
            intervals_passed = (time_since_last.total_seconds() // td.total_seconds()) + 1
            next_run = last_run + (td * int(intervals_passed))

        return next_run

    def _calculate_next_run_for_crontab(self, task) -> Optional[timezone.datetime]:
        """Calculate the next run time for a crontab schedule."""
        from django_celery_beat.schedulers import crontab_parser

        crontab = task.periodic_task.crontab
        parser = crontab_parser(60)
        next_run = parser.next(timezone.now(), crontab)
        if timezone.is_naive(next_run):
            next_run = timezone.make_aware(next_run)
        return next_run

    def _calculate_next_run_for_solar(self, task) -> Optional[timezone.datetime]:
        """Calculate the next run time for a solar schedule."""
        # Solar schedules are not supported yet
        return None

    def _calculate_next_run_for_schedule(self, task, last_run: timezone.datetime) -> Optional[timezone.datetime]:
        """Calculate the next run time for a generic schedule."""
        schedule = task.periodic_task.schedule
        if not hasattr(schedule, "run_every"):
            return None

        next_run = last_run + timezone.timedelta(seconds=schedule.run_every.total_seconds())
        now = timezone.now()

        # If next run is in the past, calculate the next occurrence from now
        if next_run < now:
            time_since_last = now - last_run
            run_every = timezone.timedelta(seconds=schedule.run_every.total_seconds())
            intervals_passed = (time_since_last.total_seconds() // run_every.total_seconds()) + 1
            next_run = last_run + (run_every * int(intervals_passed))

        return next_run

    def get_next_run(self, task) -> Optional[timezone.datetime]:
        """Get the next scheduled run time from the periodic task.

        Args:
            task: The SharedTask instance.

        Returns:
            Optional[timezone.datetime]: The next run time, or None if the task is not scheduled.
        """
        if not task.periodic_task or not task.periodic_task.enabled:
            return None

        last_run = self._get_last_run(task)
        if last_run is None:
            return timezone.now()

        # Handle different schedule types
        if task.periodic_task.interval:
            return self._calculate_next_run_for_interval(task, last_run)
        elif task.periodic_task.crontab:
            return self._calculate_next_run_for_crontab(task)
        elif task.periodic_task.solar:
            return self._calculate_next_run_for_solar(task)
        elif task.periodic_task.schedule:
            return self._calculate_next_run_for_schedule(task, last_run)

        return None
