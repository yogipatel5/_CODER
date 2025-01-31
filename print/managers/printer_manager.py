from django.db import models
from django.db.models import Q


class PrinterManager(models.Manager):
    def get_available_printers(self):
        """Get all printers that are online and ready to print"""
        return self.filter(Q(status__in=["ONLINE", "IDLE"]) & ~Q(status="INK_LOW"))

    def get_by_paper_size(self, paper_size):
        """Get printers that support a specific paper size"""
        return self.filter(default_paper_size=paper_size)

    def get_color_printers(self):
        """Get printers that support color printing"""
        return self.filter(color_capable=True)

    def get_label_printers(self):
        """Get printers specifically for label printing"""
        return self.filter(printer_type="THERMAL")

    def get_document_printers(self):
        """Get printers for standard document printing"""
        return self.filter(printer_type="INKJET")

    def get_default_printer(self):
        """Get the system default printer"""
        return self.filter(is_default=True).first()

    def update_printer_status(self, printer_id, status, error_message=None):
        """Update the status of a printer"""
        printer = self.get(id=printer_id)
        printer.status = status
        if error_message:
            printer.error_message = error_message
        printer.save(update_fields=["status", "error_message"])
        return printer

    def get_by_alias(self, alias):
        """Get a printer by its alias/nickname"""
        return self.filter(aliases__contains=[alias.lower()]).first()
