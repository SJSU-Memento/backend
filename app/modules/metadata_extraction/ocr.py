import pytesseract
from PIL.ImageFile import ImageFile

def extract_text_from_image(img: ImageFile) -> str:    
    text = pytesseract.image_to_string(img)
    
    return text
