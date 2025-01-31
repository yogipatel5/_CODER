# I want to create a label to print withniimbo_print_image command. The finished label should be 30x15mm horitzontal and using the commanbd  I want to print it. I want to use this as a label maker and an LLM will use it to gerneate a label for me based on an image and a prompt. For example, I might have an image of nuts and i want a label to print with the text Misc Nuts - I would want a label created with a icon and title in that size and printed, so it would respond in a json with the text from the image and a icon and i woudl have a service that would take that and create the label and then it would print it using the niimbot_print_image command.

import io
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont


class LabelMaker:
    def __init__(self):
        self.label_width = 300  # 30mm * 10 pixels/mm
        self.label_height = 150  # 15mm * 10 pixels/mm

    def create_label(self, text, icon_path=None):
        # Create a new white image
        label = Image.new("RGB", (self.label_width, self.label_height), "white")
        draw = ImageDraw.Draw(label)

        # If icon exists, place it on the left side
        icon_size = (100, 100) if icon_path else (0, 0)
        if icon_path:
            icon = Image.open(icon_path)
            icon = icon.resize(icon_size)
            label.paste(icon, (25, (self.label_height - icon_size[1]) // 2))

        # Add text
        font_size = 36
        font = ImageFont.truetype("Arial.ttf", font_size)
        text_position = (150 if icon_path else 25, self.label_height // 2)
        draw.text(text_position, text, fill="black", font=font, anchor="lm")

        return label

    def print_label(self, label_image):
        # Save the image temporarily
        temp_path = "temp_label.png"
        label_image.save(temp_path)

        # Print using niimbot_print_image command
        subprocess.run(["niimbot_print_image", temp_path])


def process_llm_response(llm_json):
    """
    Process the JSON response from LLM
    Expected format:
    {
        "text": "Misc Nuts",
        "icon": "path_to_icon.png"
    }
    """
    data = json.loads(llm_json)
    label_maker = LabelMaker()
    label = label_maker.create_label(data["text"], data.get("icon"))
    label_maker.print_label(label)
