# AI-Translator-Pro

Production-quality **AI Translation SaaS** platform — refactored from a Flask + vanilla JS app into a modern full-stack (React + FastAPI + AI) suitable for a software engineering internship portfolio.

## Features

- **Text translation** — Multiple languages, auto-detect source, optional grammar correction and learning-mode explanation
- **Speech translator** — Voice input (browser or server Whisper), translate, then play TTS
- **Image translation** — Upload image → OCR (pytesseract) → translate extracted text
- **Grammar correction** — Optional pre-translation correction (LanguageTool)
- **Language learning mode** — Explanation of translated sentence (extensible with LLM)
- **Translation history** — Per-user history when logged in (MongoDB)
- **Authentication** — JWT-based login/signup and protected routes
- **Responsive UI** — React + Tailwind, loading states and error handling

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│  Vite · TailwindCSS · Axios · React Router · Auth Context        │
└───────────────────────────────┬─────────────────────────────────┘
                                │ REST /api/v1/*
┌───────────────────────────────▼─────────────────────────────────┐
│                      Backend (FastAPI)                           │
│  routes/ → services/ → ai/ + database/                           │
│  translate, speech-to-text, text-to-speech, image-translate,     │
│  history, auth (login/signup)                                    │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌─────────────────┐     ┌──────────────┐
│  AI modules   │     │  MongoDB         │     │  TTS / static │
│  speech,      │     │  users,          │     │  files        │
│  translator,  │     │  translations    │     │               │
│  grammar, OCR │     └─────────────────┘     └──────────────┘
└───────────────┘
```

## Project Structure

```
AI-Translator-Pro/
├── frontend/                 # React SPA
│   ├── src/
│   │   ├── components/       # LanguageSelector, VoiceRecorder, TextInputBox, etc.
│   │   ├── context/         # AuthContext
│   │   ├── pages/           # Home, Translator, Speech, Image, Dashboard, Login, Signup
│   │   └── services/        # api.js (Axios), languages.js
│   ├── Dockerfile
│   └── package.json
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/          # translate, speech, tts, image, history, auth
│   │   ├── services/        # TranslationService, SpeechService, TTSService, etc.
│   │   ├── models/          # Pydantic schemas
│   │   ├── ai/               # speech_model, translator_model, grammar_model, ocr_model, tts_model
│   │   ├── database/         # MongoDB / in-memory
│   │   └── utils/            # config, language_handler
│   ├── requirements.txt
│   └── Dockerfile
├── ai_models/                # README pointing to backend/app/ai
├── database/                 # Schema docs (users, translations)
├── deployment/
│   ├── docker-compose.yml
│   ├── .env.example
│   └── nginx.conf (for frontend container)
└── README.md
```

## Installation

### Prerequisites

- Node 18+ and npm
- Python 3.11+
- MongoDB (optional; app falls back to in-memory store if unavailable)

### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
# Optional: set .env (copy from deployment/.env.example)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000 (Vite proxies `/api` to the backend).

### Docker (full stack)

From the repo root:

```bash
cd deployment
cp .env.example .env
# Edit .env and set SECRET_KEY
docker-compose up -d
```

- Frontend: http://localhost (port 80)
- Backend: http://localhost:8000
- MongoDB: localhost:27017

## API Documentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/translate` | Translate text (body: `text`, `src_lang`, `target_lang`, optional `correct_grammar`, `learning_mode`) |
| POST | `/api/v1/speech-to-text` | Speech to text (multipart: `file`, optional `language`) |
| POST | `/api/v1/text-to-speech` | TTS (body: `text`, `lang`) → `audio_url` |
| GET | `/api/v1/tts/file/{file_id}` | Serve TTS MP3 |
| POST | `/api/v1/image-translate` | Image → OCR + translate (multipart: `file`, `target_lang`) |
| GET | `/api/v1/history` | Translation history (auth required) |
| POST | `/api/v1/auth/login` | Login (body: `email`, `password`) → JWT |
| POST | `/api/v1/auth/signup` | Signup (body: `email`, `password`, optional `full_name`) → JWT |

OpenAPI: `/docs` and `/redoc` on the backend.

## Environment Variables

See `deployment/.env.example`. Main ones:

- `SECRET_KEY` — Required in production for JWT
- `MONGODB_URI`, `MONGODB_DB_NAME` — MongoDB connection
- `CORS_ORIGINS` — Comma-separated allowed origins
- `OPENAI_API_KEY`, `USE_WHISPER_API` — Optional Whisper API for server-side speech-to-text

## Future Improvements

- Rate limiting and request validation hardening
- Object storage (e.g. S3) for TTS files and cleanup policy
- LLM integration for richer “learning mode” explanations
- Optional Firebase instead of MongoDB
- E2E tests (Playwright/Cypress) and API tests (pytest)
- CI/CD (GitHub Actions) and production hosting notes

## License

Use as desired for portfolio and learning.
