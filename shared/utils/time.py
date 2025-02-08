"""Time formatting utilities for task management."""

from django.utils import timezone


def format_timedelta(td):
    """Format timedelta into hours and minutes.

    Args:
        td: A timedelta object

    Returns:
        str: Human readable time string
    """
    if not td:
        return "never"

    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    if hours and minutes:
        return f"{hours}hr {minutes}m"
    elif hours:
        return f"{hours}hr"
    elif minutes:
        return f"{minutes}m"
    else:
        return "just now"


def format_next_run(next_run):
    """Format next run time into human readable string.

    Args:
        next_run: A datetime object

    Returns:
        str: Human readable time string
    """
    if not next_run:
        return "—"

    now = timezone.now()
    if timezone.is_naive(next_run):
        next_run = timezone.make_aware(next_run)

    diff = next_run - now
    total_seconds = int(diff.total_seconds())

    if total_seconds < 0:
        return "now"  # Task is overdue
    elif diff.days > 0:
        return f"in {diff.days}d"
    elif total_seconds >= 3600:
        return f"in {total_seconds // 3600}h"
    elif total_seconds >= 60:
        return f"in {total_seconds // 60}m"
    else:
        return f"in {total_seconds}s"
