# AI Models

The AI/ML logic for speech, translation, grammar, and OCR lives in the backend:

- **Speech (Whisper):** `backend/app/ai/speech_model.py`
- **Translation:** `backend/app/ai/translator_model.py`
- **Grammar correction:** `backend/app/ai/grammar_model.py`
- **OCR:** `backend/app/ai/ocr_model.py`
- **TTS:** `backend/app/ai/tts_model.py`

These modules are used by the FastAPI services and can be extended (e.g. swap in a different translator or LLM) without changing the API.
