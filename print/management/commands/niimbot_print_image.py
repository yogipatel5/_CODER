import asyncio
import os

from django.core.management.base import BaseCommand, CommandError
from PIL import Image

from print.services.niimprint.printer import PrinterClient, SerialTransport


class Command(BaseCommand):
    help = "Print an image using the Niimbot printer- Image must be 30x15"

    def add_arguments(self, parser):
        parser.add_argument("image", type=str, help="Path to the image file")
        parser.add_argument("--rotate", "-r", type=int, default=0, help="Rotation angle in degrees (clockwise)")
        parser.add_argument("--density", "-d", type=int, default=3, choices=[1, 2, 3], help="Print density (1-3)")
        parser.add_argument(
            "--port", "-p", type=str, default="/dev/cu.D110-E904100934", help="Serial port for the printer"
        )

    def handle(self, *args, **options):
        """Run the async print operation"""
        return asyncio.run(self._handle(*args, **options))

    async def _handle(self, *args, **options):
        image_path = options["image"]
        rotation = options["rotate"]
        density = options["density"]
        port = options["port"]

        # Validate image path
        if not os.path.isfile(image_path):
            raise CommandError(f"Image file not found: {image_path}")

        try:
            # Create transport and printer client
            transport = SerialTransport(port=port)
            printer = PrinterClient(transport)

            # Open and process image
            image = Image.open(image_path)

            # Rotate if specified (negative for clockwise rotation)
            if rotation:
                image = image.rotate(-rotation, expand=True)

            # Print the image
            await printer.print_image(image, density=density)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully printed image: {image_path}" f" (rotation={rotation}°, density={density})"
                )
            )

        except Exception as e:
            raise CommandError(f"Failed to print image: {str(e)}")
