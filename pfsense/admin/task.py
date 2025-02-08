"""Admin configuration for Task model."""

from django.contrib import admin

from pfsense.models import Task
from shared.admin.shared_task import SharedTaskAdmin

# Register Task with SharedTaskAdmin
admin.site.register(Task, SharedTaskAdmin)
