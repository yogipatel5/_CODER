from django.db import models
from django.utils import timezone


class SharedTaskErrorManager(models.Manager):
    """Manager for SharedTaskError model with error tracking functionality."""

    def get_queryset(self):
        return super().get_queryset().select_related("task")

    def log_error(self, task, error, traceback):
        """Log an error, creating a new record or updating an existing one."""
        # Extract error information from traceback
        tb = traceback.tb_next  # Skip the current frame
        frame = tb.tb_frame
        error_type = error.__class__.__name__
        file_path = frame.f_code.co_filename
        function_name = frame.f_code.co_name
        line_number = tb.tb_lineno

        # Try to find an existing error
        error_obj = self.filter(
            task=task,
            error_type=error_type,
            file_path=file_path,
            function_name=function_name,
            line_number=line_number,
        ).first()

        if error_obj:
            # Update existing error
            error_obj.occurrence_count += 1
            error_obj.last_seen = timezone.now()
            error_obj.error_message = str(error)

            # Update status based on current state
            if error_obj.status == self.model.Status.CLEARED:
                error_obj.status = self.model.Status.ONGOING
                error_obj.cleared = False
                error_obj.cleared_at = None
                error_obj.cleared_by = None
            elif error_obj.status == self.model.Status.REGRESSED:
                error_obj.status = self.model.Status.ONGOING
            elif error_obj.status == self.model.Status.NEW:
                error_obj.status = self.model.Status.ONGOING

            error_obj.save()
        else:
            # Create new error
            error_obj = self.create(
                task=task,
                error_type=error_type,
                file_path=file_path,
                function_name=function_name,
                line_number=line_number,
                error_message=str(error),
                status=self.model.Status.NEW,
            )

        return error_obj

    def update_regressed_errors(self, task):
        """Update errors that didn't occur in the last run to regressed status."""
        self.filter(
            task=task,
            status__in=[self.model.Status.NEW, self.model.Status.ONGOING],
            last_seen__lt=timezone.now() - timezone.timedelta(minutes=1),  # If not seen in last minute
        ).update(status=self.model.Status.REGRESSED)

    def clear(self, user=None):
        """Clear this error."""
        return self.update(
            cleared=True,
            cleared_at=timezone.now(),
            cleared_by=user,
            status=self.model.Status.CLEARED,
        )
