from io import BytesIO
from typing import NamedTuple

from PIL import Image

from app.modules.image_metadata_extraction.description import describe_image
from app.modules.image_metadata_extraction.ocr import extract_text_from_image

class ImageMetadata(NamedTuple):
    description: str
    ocr: str


def extract_metadata_from_image(content: bytes):
    image = BytesIO(content)
    image_file = Image.open(image)
    description = describe_image(image_file)
    ocr = extract_text_from_image(image_file)

    return ImageMetadata(description=description, ocr=ocr)

