from io import BytesIO
#BytesIO wraps the bytes in an in-memory file-like object
#because we have image_bytes in oue end points Those are raw bytes stored in memory. 
# Image.open() expects something that behaves like a file.
import pytesseract # pytesseract calls the Tesseract program from Python.
from PIL import Image #Pillow opens and processes image data in Python.
from app.services.image_processor import preprocess_image

def extract_text(image_bytes: bytes) -> str:
    with Image.open(BytesIO(image_bytes)) as image:
        processed_image = preprocess_image(image)
        extracted_text = pytesseract.image_to_string(processed_image)

    return extracted_text.strip()

