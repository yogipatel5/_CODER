from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html


def format_timedelta(td):
    """Format timedelta into hours and minutes."""
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


class SharedTaskAdmin(admin.ModelAdmin):
    """Base admin class for Task models."""

    list_display = [
        "name",
        "description",
        "is_active",
        "get_last_run_display",
        "last_status",
        "get_next_run_display",
        "schedule",
        "notify_on_error",
        "get_error_count_display",
        "action_buttons",
    ]
    list_filter = ["is_active", "last_status", "notify_on_error"]
    search_fields = ["name", "description"]
    readonly_fields = ["last_run", "next_run", "last_status", "last_result", "last_error"]
    save_on_top = True
    actions = ["clear_task_errors"]

    fieldsets = (
        (None, {"fields": ("name", "description"), "classes": ("wide",)}),
        (
            "Task Settings",
            {
                "fields": ("is_active", "notify_on_error", "disable_on_error", "max_retries"),
                "classes": ("collapse",),
            },
        ),
        (
            "Schedule",
            {
                "fields": ("schedule", "periodic_task", "last_run", "next_run"),
                "classes": ("collapse",),
            },
        ),
        (
            "Execution Results",
            {
                "fields": ("last_status", "last_result", "last_error"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_list_display(self, request):
        """Allow subclasses to extend list_display."""
        return list(self.list_display)

    def get_list_filter(self, request):
        """Allow subclasses to extend list_filter."""
        return list(self.list_filter)

    def get_search_fields(self, request):
        """Allow subclasses to extend search_fields."""
        return list(self.search_fields)

    def get_readonly_fields(self, request, obj=None):
        """Allow subclasses to extend readonly_fields."""
        return list(self.readonly_fields)

    def get_error_count_display(self, obj):
        """Display count of active errors."""
        return obj.error_count_display

    get_error_count_display.short_description = "Active Errors"

    def get_last_run_display(self, obj):
        """Format last run time."""
        return obj.last_run_display

    get_last_run_display.short_description = "Last Run"
    get_last_run_display.admin_order_field = "last_run"

    def get_next_run_display(self, obj):
        """Format next run time."""
        return obj.next_run_display

    get_next_run_display.short_description = "Next Run"
    get_next_run_display.admin_order_field = "next_run"

    def clear_task_errors(self, request, queryset):
        """Clear all errors for selected tasks."""
        for task in queryset:
            task.errors.filter(cleared=False).update(cleared=True, cleared_at=timezone.now(), cleared_by=request.user)
        self.message_user(request, f"Cleared errors for {queryset.count()} tasks.")

    clear_task_errors.short_description = "Clear errors for selected tasks"

    def action_buttons(self, obj):
        """Display action buttons based on task state."""
        buttons = []

        # Run Now button
        run_url = reverse(
            f"admin:{obj._meta.app_label}_{obj._meta.model_name}_run",
            args=[obj.pk],
        )
        buttons.append(f'<a class="button" href="{run_url}">Run Now</a>')

        # Clear Errors button (only if there are errors)
        if obj.errors.filter(cleared=False).exists():
            clear_url = reverse(
                f"admin:{obj._meta.app_label}_{obj._meta.model_name}_clear_errors",
                args=[obj.pk],
            )
            buttons.append(f'<a class="button" href="{clear_url}">Clear Errors</a>')

        return format_html("&nbsp;".join(buttons))

    action_buttons.short_description = "Actions"
    action_buttons.allow_tags = True

    def get_urls(self):
        """Add custom URLs for task actions."""
        info = self.model._meta.app_label, self.model._meta.model_name
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:task_id>/run/",
                self.admin_site.admin_view(self.run_task_view),
                name=f"{info[0]}_{info[1]}_run",
            ),
            path(
                "<int:task_id>/clear-errors/",
                self.admin_site.admin_view(self.clear_errors_view),
                name=f"{info[0]}_{info[1]}_clear_errors",
            ),
        ]
        return custom_urls + urls

    def run_task_view(self, request, task_id):
        """View for running a task manually."""
        task = self.model.objects.get(pk=task_id)
        task.run()
        self.message_user(request, f"Task '{task.name}' has been queued to run.")
        return redirect("..")

    def clear_errors_view(self, request, task_id):
        """View for clearing all errors for a task."""
        task = self.model.objects.get(pk=task_id)
        count = task.errors.filter(cleared=False).update(
            cleared=True, cleared_at=timezone.now(), cleared_by=request.user
        )
        self.message_user(request, f"Cleared {count} errors for task '{task.name}'.")
        return redirect("..")
