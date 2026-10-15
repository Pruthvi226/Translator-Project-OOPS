"""Synthetic native Tesseract smoke check, not an OCR accuracy benchmark."""
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from backend.app.services.media import extract_image

image = Image.new('RGB', (900, 180), 'white')
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 64)
ImageDraw.Draw(image).text((35, 40), 'Hello world 123', font=font, fill='black')
stream = BytesIO()
image.save(stream, format='PNG')
result = extract_image(stream.getvalue(), 'eng')
assert 'Hello' in result and '123' in result, repr(result)
print('Native Tesseract/OpenCV image pipeline smoke check passed (synthetic image only).')
