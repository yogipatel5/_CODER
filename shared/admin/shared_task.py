import logging

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html

from shared.utils.time import format_next_run, format_timedelta

logger = logging.getLogger(__name__)


class SharedTaskErrorInline(admin.TabularInline):
    """Inline admin for TaskError model."""

    model = None  # Set this in your app's admin.py
    extra = 0
    readonly_fields = (
        "error_type",
        "error_message",
        "file_path",
        "function_name",
        "line_number",
        "occurrence_count",
        "first_seen",
        "last_seen",
        "cleared",
        "cleared_at",
        "cleared_by",
    )
    can_delete = False
    max_num = 0
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


class SharedTaskErrorAdmin(admin.ModelAdmin):
    """Admin interface for TaskError model."""

    list_display = (
        "task",
        "error_type",
        "function_name",
        "occurrence_count",
        "last_seen",
        "cleared",
    )
    list_filter = ("cleared", "error_type", "task")
    search_fields = ("error_message", "function_name", "file_path")
    readonly_fields = (
        "task",
        "error_type",
        "error_message",
        "file_path",
        "function_name",
        "line_number",
        "occurrence_count",
        "first_seen",
        "last_seen",
        "cleared",
        "cleared_at",
        "cleared_by",
    )
    actions = ["clear_errors"]
    list_display_links = ("error_type",)
    save_on_top = True

    def has_add_permission(self, request):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("task")

    def clear_errors(self, request, queryset):
        for error in queryset:
            error.clear(request.user)
        self.message_user(request, f"Cleared {queryset.count()} errors.")

    clear_errors.short_description = "Clear selected errors"


class SharedTaskAdmin(admin.ModelAdmin):
    """Base admin class for Task models."""

    list_display = [
        "name",
        "description",
        "is_active",
        "get_last_run_display",
        "last_status",
        "get_last_result_display",
        "get_next_run_display",
        "schedule",
        "notify_on_error",
        "get_error_count_display",
        "action_buttons",
    ]
    list_filter = ["is_active", "last_status", "notify_on_error"]
    search_fields = ["name", "description"]
    readonly_fields = [
        "last_run",
        "get_next_run_display",
        "last_status",
        "get_last_result_display",
        "last_error",
    ]
    save_on_top = True
    actions = ["clear_task_errors", "enable_tasks", "disable_tasks", "run_tasks"]
    inlines = []  # Add TaskErrorInline in your app's admin.py

    fieldsets = (
        (None, {"fields": ("name", "description"), "classes": ("wide",)}),
        (
            "Task Settings",
            {
                "fields": ("is_active", "notify_on_error"),
                "classes": ("collapse",),
            },
        ),
        (
            "Schedule",
            {
                "fields": ("periodic_task", "last_run", "get_next_run_display"),
                "classes": ("collapse",),
            },
        ),
        (
            "Execution Results",
            {
                "fields": ("last_status", "get_last_result_display", "last_error"),
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

    def get_queryset(self, request):
        """Optimize queryset by prefetching related fields."""
        return super().get_queryset(request).prefetch_related("errors").select_related("periodic_task")

    def get_error_count_display(self, obj):
        """Display count of active errors."""
        count = obj.errors.filter(cleared=False).count()
        if count == 0:
            return "—"
        return format_html(
            '<span style="color: red;">{}</span>',
            count,
        )

    get_error_count_display.short_description = "Active Errors"

    def get_last_run_display(self, obj):
        """Format last run time."""
        if not obj.last_run:
            return "never"
        return format_timedelta(timezone.now() - obj.last_run)

    get_last_run_display.short_description = "Last Run"
    get_last_run_display.admin_order_field = "last_run"

    def get_last_result_display(self, obj):
        """Format last result without JSON quotes."""
        if obj.last_result is None:
            return "-"
        if isinstance(obj.last_result, str):
            return obj.last_result
        return str(obj.last_result)

    get_last_result_display.short_description = "Last result"
    get_last_result_display.admin_order_field = "last_result"

    def get_next_run_display(self, obj):
        """Format next run time."""
        logger.info("Getting next run display for %s", obj)
        if not obj.periodic_task or not obj.periodic_task.enabled:
            logger.info("Task %s is not enabled", obj.name)
            return "—"

        # Get the schedule
        schedule = None
        if hasattr(obj.periodic_task, "interval"):
            logger.info("Interval schedule for %s", obj)
            schedule = obj.periodic_task.interval
            logger.info("Interval schedule: %s", schedule)
        elif hasattr(obj.periodic_task, "crontab"):
            logger.info("Crontab schedule for %s", obj)
            schedule = obj.periodic_task.crontab
        elif hasattr(obj.periodic_task, "solar"):
            logger.info("Solar schedule for %s", obj)
            schedule = obj.periodic_task.solar

        if not schedule:
            logger.info("No schedule found for %s", obj)
            return "—"

        # Get last run time, defaulting to now if never run
        last_run = obj.periodic_task.last_run_at or timezone.now()
        if timezone.is_naive(last_run):
            last_run = timezone.make_aware(last_run)

        try:
            # Calculate next run time using the appropriate schedule type
            logger.info("Calculating next run for %s", obj)
            if hasattr(obj.periodic_task, "interval"):
                next_run = last_run + schedule.schedule.run_every
            elif hasattr(obj.periodic_task, "crontab"):
                next_run = schedule.schedule.now()
            elif hasattr(obj.periodic_task, "solar"):
                next_run = schedule.schedule.now()
            else:
                next_run = None

            logger.info("Next run: %s", next_run)
            return format_next_run(next_run)
        except Exception:
            logger.exception("Error calculating next run for %s", obj)
            return "—"

    get_next_run_display.short_description = "Next Run"

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
        task = self.get_object(request, task_id)
        self.model.objects.run_task(task)
        self.message_user(request, f"Task '{task.name}' has been queued to run.")

        # Get the referring page, fallback to the changelist if not available
        referer = request.META.get("HTTP_REFERER")
        if not referer:
            return redirect(
                "admin:{}_{}_changelist".format(
                    task._meta.app_label,
                    task._meta.model_name,
                )
            )
        return redirect(referer)

    def clear_errors_view(self, request, task_id):
        """View for clearing all errors for a task."""
        task = self.get_object(request, task_id)
        count = task.errors.filter(cleared=False).update(
            cleared=True, cleared_at=timezone.now(), cleared_by=request.user
        )
        self.message_user(request, f"Cleared {count} errors for task '{task.name}'.")
        return redirect("..")

    def enable_tasks(self, request, queryset):
        for task in queryset:
            task.is_active = True
            task.save()
        self.message_user(request, f"Enabled {queryset.count()} tasks.")

    enable_tasks.short_description = "Enable selected tasks"

    def disable_tasks(self, request, queryset):
        for task in queryset:
            task.is_active = False
            task.save()
        self.message_user(request, f"Disabled {queryset.count()} tasks.")

    disable_tasks.short_description = "Disable selected tasks"

    def run_tasks(self, request, queryset):
        for task in queryset:
            task.objects.run_task(task)
        self.message_user(request, f"Started {queryset.count()} tasks.")

    run_tasks.short_description = "Run selected tasks"
