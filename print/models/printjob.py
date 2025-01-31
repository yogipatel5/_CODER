from django.core.validators import MinValueValidator
from django.db import models

from print.models.printer import ColorModel, PaperSize, Printer

from ..managers.printjob_manager import PrintJobManager


class PrintJobStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PROCESSING = "PROCESSING", "Processing"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class PrintJob(models.Model):
    """
    Represents a print job in the system.

    A print job is created when a user requests to print a file or URL.
    It tracks the status of the print request and stores all necessary
    print settings and file information.
    """

    # Core Fields
    printer = models.ForeignKey(
        Printer, on_delete=models.CASCADE, related_name="print_jobs", help_text="Printer to handle this job"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # File Details
    file_name = models.CharField(max_length=255, help_text="Original name of the file to print")
    file_type = models.CharField(max_length=50, help_text="MIME type or file extension")
    file_size = models.BigIntegerField(help_text="Size of file in bytes")
    file_url = models.URLField(max_length=500, null=True, blank=True, help_text="URL for remote files")
    file_hash = models.CharField(max_length=64, help_text="SHA-256 hash of file for integrity")

    # Status Tracking
    status = models.CharField(
        max_length=20,
        choices=PrintJobStatus.choices,
        default=PrintJobStatus.PENDING,
        help_text="Current status of the print job",
    )
    started_at = models.DateTimeField(null=True, blank=True, help_text="When job started processing")
    completed_at = models.DateTimeField(null=True, blank=True, help_text="When job completed or failed")
    error_message = models.TextField(null=True, blank=True, help_text="Error message if job failed")
    retry_count = models.IntegerField(default=0, help_text="Number of retry attempts")

    # Print Settings
    copies = models.IntegerField(default=1, validators=[MinValueValidator(1)], help_text="Number of copies to print")
    paper_size = models.CharField(max_length=20, choices=PaperSize.choices, help_text="Paper size for this job")
    color_mode = models.CharField(max_length=20, choices=ColorModel.choices, help_text="Color mode for this job")
    duplex = models.BooleanField(default=False, help_text="Whether to print double-sided")
    custom_settings = models.JSONField(default=dict, help_text="Additional printer-specific settings for this job")

    objects = PrintJobManager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["printer", "status"]),
        ]
        verbose_name = "Print Job"
        verbose_name_plural = "Print Jobs"

    def __str__(self):
        return f"{self.file_name} ({self.get_status_display()})"

    @property
    def is_active(self):
        """Whether the job is currently being processed"""
        return self.status in [PrintJobStatus.PENDING, PrintJobStatus.PROCESSING]

    @property
    def is_finished(self):
        """Whether the job has reached a terminal state"""
        return self.status in [PrintJobStatus.COMPLETED, PrintJobStatus.FAILED, PrintJobStatus.CANCELLED]

    def get_duration(self):
        """Get the duration of the print job if completed"""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        return None
