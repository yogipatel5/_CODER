from django.db import models

from ..managers.printer_manager import PrinterManager


class PaperSize(models.TextChoices):
    LETTER = "LETTER", "Letter (8.5 x 11)"
    LETTER_FULL = "LETTER_FULL", "Letter Fullbleed"
    LEGAL = "LEGAL", "Legal (8.5 x 14)"
    LABEL_4X6 = "4X6", "Label (4 x 6)"
    A4 = "A4", "A4"
    LABEL_4XL = "LABEL_4XL", "4 x 6 Label"
    LABEL_12MM = "LABEL_12MM", "12mm Label"
    LABEL_30x15 = "LABEL_30x15", "30mm x 15mm Label"
    CUSTOM = "CUSTOM", "Custom"


class PrinterType(models.TextChoices):
    INKJET = "INKJET", "Inkjet Printer"
    THERMAL = "THERMAL", "Thermal Printer"
    BLUETOOTH = "BLUETOOTH", "Bluetooth Label Printer"


class ConnectionType(models.TextChoices):
    CUPS = "CUPS", "CUPS Network Printer"
    BLUETOOTH = "BLUETOOTH", "Bluetooth Device"
    USB = "USB", "USB Serial Device"


class PrinterStatus(models.TextChoices):
    ONLINE = "ONLINE", "Online"
    OFFLINE = "OFFLINE", "Offline"
    INK_LOW = "INK_LOW", "Ink Low"
    IDLE = "IDLE", "Idle"


class PrintQuality(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    NORMAL = "NORMAL", "Normal"
    HIGH = "HIGH", "High"
    TEXT = "TEXT", "Text Only"
    GRAPHICS = "GRAPHICS", "Graphics"


class ColorModel(models.TextChoices):
    GRAY = "GRAY", "Grayscale"
    RGB = "RGB", "Color"


class MediaType(models.TextChoices):
    ANY = "ANY", "Any"
    STATIONERY = "STATIONERY", "Plain Paper"
    PHOTO_GLOSSY = "PHOTO_GLOSSY", "Photo Glossy"
    HEAVY = "HEAVY", "Heavy Paper"
    LIGHT = "LIGHT", "Light Paper"
    CONTINUOUS = "CONTINUOUS", "Continuous Paper"
    LABELS = "LABELS", "Labels"


class Printer(models.Model):
    # Basic Information
    name = models.CharField(max_length=100, help_text="Printer name (e.g., HP OfficeJet Pro 8720)")
    model = models.CharField(max_length=100, help_text="Model number/name")
    device_name = models.CharField(max_length=100, help_text="Network device name (CUPS name) or Bluetooth address")
    location = models.CharField(max_length=100, help_text="Physical location of printer")
    aliases = models.JSONField(default=list, help_text="List of aliases/nicknames for this printer")
    printer_type = models.CharField(
        max_length=20, choices=PrinterType.choices, help_text="Type of printer (e.g., INKJET, THERMAL, BLUETOOTH)"
    )
    connection_type = models.CharField(
        max_length=20,
        choices=ConnectionType.choices,
        default=ConnectionType.CUPS,
        help_text="How to connect to this printer",
    )
    bluetooth_address = models.CharField(
        max_length=100, null=True, blank=True, help_text="Bluetooth MAC address for Bluetooth printers"
    )

    # Network Information
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address for network printing")
    airprint_enabled = models.BooleanField(default=False, help_text="Whether AirPrint is enabled")
    is_default = models.BooleanField(default=False, help_text="Whether this is the system default printer")

    # Status Information
    status = models.CharField(
        max_length=20, choices=PrinterStatus.choices, default=PrinterStatus.OFFLINE, help_text="Current printer status"
    )
    driver_version = models.CharField(max_length=20, blank=True, help_text="Printer driver version")

    # Print Settings
    default_paper_size = models.CharField(
        max_length=20, choices=PaperSize.choices, help_text="Default paper size for this printer"
    )
    custom_paper_width = models.IntegerField(
        null=True, blank=True, help_text="Custom paper width in points (1/72 inch)"
    )
    custom_paper_height = models.IntegerField(
        null=True, blank=True, help_text="Custom paper height in points (1/72 inch)"
    )
    default_media_type = models.CharField(
        max_length=20, choices=MediaType.choices, default=MediaType.ANY, help_text="Default media type"
    )
    default_print_quality = models.CharField(
        max_length=20, choices=PrintQuality.choices, default=PrintQuality.NORMAL, help_text="Default print quality"
    )
    default_color_model = models.CharField(
        max_length=20, choices=ColorModel.choices, default=ColorModel.RGB, help_text="Default color mode"
    )

    # Capabilities
    color_capable = models.BooleanField(default=True, help_text="Whether printer can print in color")
    duplex_capable = models.BooleanField(default=False, help_text="Whether printer supports double-sided printing")
    supports_custom_paper_size = models.BooleanField(
        default=False, help_text="Whether printer supports custom paper sizes"
    )
    resolution_dpi = models.IntegerField(default=300, help_text="Print resolution in DPI")

    # CUPS Options (stored as JSON for printer-specific options)
    cups_options = models.JSONField(default=dict, help_text="Additional CUPS options specific to this printer")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PrinterManager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.location})"

    @property
    def is_online(self):
        return self.status in [PrinterStatus.ONLINE, PrinterStatus.IDLE, PrinterStatus.INK_LOW]

    def get_cups_name(self):
        """Return the CUPS printer name (device_name with spaces replaced by underscores)"""
        return self.device_name.replace(" ", "_")
