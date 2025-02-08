"""Admin configuration for notion app."""

from django.contrib import admin

from notion.models import Task
from shared.admin import SharedTaskAdmin

# Register Task with SharedTaskAdmin
admin.site.register(Task, SharedTaskAdmin)
