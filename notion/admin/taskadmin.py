from django.contrib import admin

# Import your models here
from notion.models.task import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "last_run", "error_count"]
    list_filter = ["is_active", "notify_on_error", "disable_on_error"]
    search_fields = ["name", "description"]
    readonly_fields = ["last_run", "next_run", "error_count", "last_error", "last_error_time"]
