from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import warnings
import zipfile
from fastapi import HTTPException, UploadFile
from ..ai.providers import ProviderUnavailable

IMAGE_TYPES = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}
AUDIO_TYPES = {'.wav': 'audio/wav', '.mp3': 'audio/mpeg', '.m4a': 'audio/mp4', '.ogg': 'audio/ogg', '.webm': 'audio/webm', '.flac': 'audio/flac'}
DOC_TYPES = {'.txt': 'text/plain', '.pdf': 'application/pdf', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}


async def read_upload(file: UploadFile, allowed, limit):
    try:
        suffix = Path(file.filename or '').suffix.lower()
        if suffix not in allowed:
            raise HTTPException(415, 'Unsupported file type')
        valid_types = {allowed[suffix], 'application/octet-stream'}
        if suffix == '.wav':
            valid_types.add('audio/x-wav')
        if suffix == '.m4a':
            valid_types.add('audio/x-m4a')
        if suffix == '.flac':
            valid_types.add('audio/x-flac')
        if file.content_type not in valid_types:
            raise HTTPException(415, 'File extension and content type do not match')
        data = await file.read(limit + 1)
        if not data or len(data) > limit:
            raise HTTPException(413, 'File is empty or exceeds upload limit')
        return data, suffix
    finally:
        await file.close()


def extract_image(data, language='eng'):
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = 20_000_000
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            image = Image.open(BytesIO(data))
            if image.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError('Unsupported image encoding')
            image.load()
            image = ImageOps.exif_transpose(image).convert('RGB')
            gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    except Exception:
        raise HTTPException(422, 'Invalid image or image dimensions exceed limit') from None
    try:
        # Tesseract's layout analysis provides block/line reading order.
        text = pytesseract.image_to_string(gray, lang=language, config='--psm 3', timeout=30).strip()
    except Exception:
        raise ProviderUnavailable('OCR unavailable; install Tesseract and requested language packs') from None
    if not text:
        raise HTTPException(422, 'No readable text found in image')
    return text


@lru_cache(maxsize=1)
def whisper_model(model_name):
    from faster_whisper import WhisperModel
    return WhisperModel(model_name, device='cpu', compute_type='int8')


def transcribe(data, suffix, model_name):
    import av
    with TemporaryDirectory(prefix='fluentflow-') as directory:
        path = Path(directory) / ('audio' + suffix)
        path.write_bytes(data)
        try:
            # Decode a bounded duration before invoking a costly model.
            with av.open(str(path)) as audio:
                streams = [s for s in audio.streams if s.type == 'audio']
                if not streams:
                    raise ValueError('No audio stream')
                duration = audio.duration / av.time_base if audio.duration else None
                if duration is None or duration > 300:
                    raise ValueError('Unknown or excessive duration')
        except Exception:
            raise HTTPException(422, 'Audio must decode successfully and be at most 5 minutes') from None
        segments, info = whisper_model(model_name).transcribe(str(path), beam_size=3, vad_filter=True)
        text = ' '.join(s.text.strip() for s in segments).strip()
        if not text:
            raise HTTPException(422, 'No speech detected')
        return {'transcription': text, 'detected_language': info.language}


def synthesize(text, language):
    from gtts import gTTS
    from gtts.lang import tts_langs
    if language not in tts_langs():
        raise HTTPException(422, 'Speech synthesis does not support this language')
    stream = BytesIO()
    gTTS(text=text, lang=language, timeout=(5, 25)).write_to_fp(stream)
    return stream.getvalue()


def extract_document(data, suffix):
    """Paragraph-level structure, not arbitrary PDF visual layout."""
    try:
        if suffix == '.txt':
            text = data.decode('utf-8-sig')
            blocks = text.split('\n')
        elif suffix == '.pdf':
            from pypdf import PdfReader
            if not data.startswith(b'%PDF-'):
                raise ValueError('Not a PDF')
            reader = PdfReader(BytesIO(data))
            if reader.is_encrypted or len(reader.pages) > 100:
                raise ValueError('Encrypted or too many pages')
            blocks = [(page.extract_text() or '') for page in reader.pages]
        else:
            from docx import Document
            from docx.text.paragraph import Paragraph
            with zipfile.ZipFile(BytesIO(data)) as archive:
                if sum(f.file_size for f in archive.infolist()) > 30_000_000:
                    raise ValueError('Expanded document too large')
                if len(archive.infolist()) > 2000:
                    raise ValueError('Too many archive entries')
            document = Document(BytesIO(data))
            blocks = []
            for block in document.iter_inner_content():
                if isinstance(block, Paragraph):
                    blocks.append(block.text)
                else:
                    for row in block.rows:
                        blocks.append('\t'.join(cell.text for cell in row.cells))
        text = '\n'.join(blocks)
        if not text.strip() or len(text) > 50000:
            raise ValueError('Empty or too long')
        return text
    except Exception:
        raise HTTPException(422, 'Document must contain 1–50,000 text characters, be unencrypted, and have at most 100 PDF pages') from None


def export_docx(text):
    from docx import Document
    document = Document()
    for line in text.split('\n'):
        document.add_paragraph(line)
    stream = BytesIO()
    document.save(stream)
    return stream.getvalue()
