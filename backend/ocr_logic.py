import pytesseract
from pytesseract import image_to_string
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image

# Set the path to the installed Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_tesseract(image_path):
    """Extract text from an image using Tesseract OCR."""
    try:
        image = Image.open(image_path)
        text = image_to_string(image)
        return text
    except Exception as e:
        return f"[Tesseract Error] {e}"

def extract_text_aya_vision(image_path):
    """Extract text from an image using the Aya Vision transformer model."""
    try:
        model_id = "CohereForAI/aya-vision-8b"
        processor = AutoProcessor.from_pretrained(model_id)
        model = AutoModelForImageTextToText.from_pretrained(model_id)

        image = Image.open(image_path)
        inputs = processor(images=image, return_tensors="pt")
        outputs = model.generate(**inputs)
        text = processor.decode(outputs[0], skip_special_tokens=True)

        return text
    except Exception as e:
        return f"[Aya Vision Error] {e}"