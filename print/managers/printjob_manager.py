from django.db import models
from django.utils import timezone


class PrintJobManager(models.Manager):
    def get_active_jobs(self):
        """Get all jobs that are currently pending or processing"""
        return self.filter(status__in=["PENDING", "PROCESSING"]).order_by("created_at")

    def get_jobs_by_printer(self, printer_id):
        """Get all jobs for a specific printer"""
        return self.filter(printer_id=printer_id).order_by("-created_at")

    def get_failed_jobs(self):
        """Get all failed jobs that might need attention"""
        return self.filter(status="FAILED").order_by("-created_at")

    def get_jobs_in_last_24h(self):
        """Get all jobs from the last 24 hours"""
        yesterday = timezone.now() - timezone.timedelta(days=1)
        return self.filter(created_at__gte=yesterday).order_by("-created_at")

    def create_job(self, printer, file_name, file_type, file_size, **kwargs):
        """Create a new print job with the given parameters"""
        return self.create(
            printer=printer, file_name=file_name, file_type=file_type, file_size=file_size, status="PENDING", **kwargs
        )

    def mark_job_started(self, job_id):
        """Mark a job as started"""
        job = self.get(id=job_id)
        job.status = "PROCESSING"
        job.started_at = timezone.now()
        job.save(update_fields=["status", "started_at"])
        return job

    def mark_job_completed(self, job_id, error_message=None):
        """Mark a job as completed or failed"""
        job = self.get(id=job_id)
        job.completed_at = timezone.now()

        if error_message:
            job.status = "FAILED"
            job.error_message = error_message
            job.retry_count += 1
        else:
            job.status = "COMPLETED"

        job.save(update_fields=["status", "completed_at", "error_message", "retry_count"])
        return job

    def retry_failed_jobs(self, max_retries=3):
        """Reset failed jobs for retry if they haven't exceeded max_retries"""
        return self.filter(status="FAILED", retry_count__lt=max_retries).update(
            status="PENDING", error_message=None, started_at=None, completed_at=None
        )
