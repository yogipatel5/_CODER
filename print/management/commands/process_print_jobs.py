from django.core.management.base import BaseCommand
from django.db import transaction

from print.models import PrintJob
from print.services.print_service import PrintService


class Command(BaseCommand):
    help = "Process pending print jobs"

    def add_arguments(self, parser):
        parser.add_argument("--job-id", type=int, help="Process a specific job ID")
        parser.add_argument("--printer", type=str, help="Process jobs for a specific printer")

    def handle(self, *args, **options):
        service = PrintService()

        # Get jobs to process
        jobs = PrintJob.objects.get_active_jobs()

        if options["job_id"]:
            jobs = jobs.filter(id=options["job_id"])

        if options["printer"]:
            jobs = jobs.filter(printer__name__icontains=options["printer"])

        if not jobs:
            self.stdout.write("No pending jobs found")
            return

        # Process each job
        for job in jobs:
            try:
                with transaction.atomic():
                    cups_job_id = service.print_job(job)
                    self.stdout.write(
                        self.style.SUCCESS(f"Successfully processed job {job.id} " f"(CUPS job {cups_job_id})")
                    )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to process job {job.id}: {str(e)}"))
