# 🌟 Fluent Flow AI — Advanced LLM Translator & Language Tutor

<p align="center">
  <img src="/static/images/Translator-App.jpg" alt="Fluent Flow AI Cover" width="100%" style="border-radius: 16px; box-shadow: 0 8px 32px rgba(99, 102, 241, 0.3); margin-bottom: 20px;" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python Badge" />
  <img src="https://img.shields.io/badge/Flask-v3.1.0-darkgreen?style=for-the-badge&logo=flask&logoColor=white" alt="Flask Badge" />
  <img src="https://img.shields.io/badge/Google--Gemini--AI-Active-purple?style=for-the-badge&logo=google&logoColor=white" alt="Gemini Badge" />
  <img src="https://img.shields.io/badge/Docker-Compatible-blue?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Badge" />
  <img src="https://img.shields.io/badge/UI--UX-Glassmorphic-pink?style=for-the-badge" alt="UI-UX Badge" />
</p>

---

## 📖 Overview

**Fluent Flow AI** is a state-of-the-art, single-page translation platform that converts standard machine translation into an **interactive cognitive language tutoring portal**. 

Built with an **OOP-architected Flask backend** and powered by the **Google Gemini LLM**, the application provides context-sensitive, tone-adjustable translations, rich linguistic insights, and an inline AI Tutor Chat widget. It is styled with a **premium, glassmorphic dark/light interface** that operates with resilient, graceful fallback systems—working seamlessly out-of-the-box even without an API key.

---

## ✨ Features

### 🧠 Advanced AI Capabilities (Google Gemini)
*   **Contextual Tone Translation:** Tailor translations with 6 target tones: *Professional, Formal, Casual, Academic, Creative/Poetic,* or *Slang/Idiomatic*.
*   **Linguistic Insights Breakdown:** Automatically isolates grammatical structures, compiles interactive vocabulary spotlights (Markdown tables), and reveals cultural nuances.
*   **Interactive AI Tutor Chat:** Real-time conversational tutoring. Ask *Fluent Flow AI* questions directly about pronunciation, syntax, or alternate synonyms.
*   **Resilient Fallback Mode:** Seamlessly reverts to free standard translations (`deep-translator` and local `gTTS`) if no `GEMINI_API_KEY` is present.

### 🎨 Stunning Glassmorphic UI/UX
*   **Modern Aesthetics:** Deep ambient backglows, semi-transparent frosted cards (`backdrop-filter`), glowing indicators, and custom scrollbars.
*   **Theme Engine:** Smooth switches between Default Dark mode (indigo-neon glows) and Light mode (soft, clean, pastel layers) with memory retention via `localStorage`.
*   **Micro-Animations:** Skeleton shimmer loader blocks, pulsate voice dictation indicators, checkmark clipboard confirmations, and custom toast alerts.
*   **Searchable Pickers:** Seamless select fields powered by customized TomSelect overrides.
*   **Speech Integration:** Built-in web voice dictation (microphone capture) and text-to-speech (speak aloud).

### 🐳 Developer-First DevOps
*   **Dockerized Services:** Single-command workspace compilation using a lightweight `python:3.11-slim` container.
*   **Production Runner:** The container serves Flask through Gunicorn with a built-in healthcheck.
*   **Isolated Environments:** Clean `.env.example` configurations.

---

## 🛠️ Technology Stack

*   **Backend:** Python 3.10+, Flask, `google-generativeai`, `deep-translator`, `gtts`, `python-dotenv`.
*   **Frontend:** HTML5 (Semantic Structure), CSS3 (Custom Design System, Flexbox, Grid, Glassmorphic parameters), JavaScript (ES6 classes, DOM state handlers, custom markdown parser).
*   **DevOps:** Docker, Docker Compose, Gunicorn (production runner ready).

---

## 📁 Repository Structure

```
fluent-flow-ai/
├── app.py                   # OOP Flask application (API Routing & Fallback logic)
├── requirements.txt         # Upgraded backend dependencies
├── Dockerfile               # Slim production-ready Docker deployment file
├── docker-compose.yml       # Docker Compose service mapping localhost:5001 to the app
├── .dockerignore            # Build exclusion rules
├── .env                     # Local secrets configuration (ignored in Git)
├── .env.example             # Configuration settings template
├── templates/
│   └── index.html           # Core HTML skeleton and layout grids
└── static/
    ├── style.css            # Responsive CSS design system (Dark/Light)
    ├── script.js            # TomSelect config, Speech STT, MD compiler, Chat state
    └── images/
        ├── Translator-App.jpg
        └── Translator-App_1.jpg
```

---

## 🚀 Getting Started

Ensure you have **Docker Desktop** installed.

### Step 1: Clone and Set Up Secrets
1. Navigate to the project directory:
   ```bash
   cd frontend_1
   ```
2. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
3. Edit the `.env` file and insert your free Gemini API key:
   ```env
   GEMINI_API_KEY=your_google_gemini_api_key_here
   ```
   *(Create a free key at [Google AI Studio](https://aistudio.google.com/). If left blank, standard mode continues seamlessly!)*

---

### Step 2: Choose Your Execution Method

#### 🐳 Method A: Run inside Docker (Recommended)
1. Build the container and start the services:
   ```bash
   docker compose up --build
   ```
2. Open your browser and navigate to:
   ```
   http://localhost:5001
   ```
*Tip: The container uses port `5001` on the host because port `5000` may already be used by another local service.*

---

#### 🐍 Method B: Run Locally (Without Docker)
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the Flask application:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000
   ```

---

## 🔌 API Endpoints Breakdown

| Route | Method | Payload | Description |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | None | Renders main frontend index template |
| `/ai-status` | `GET` | None | Informs client if Gemini services are active |
| `/translate` | `POST` | `{ text, src_lang, target_lang, use_ai, tone }` | Routes translation request to standard vs LLM parser |
| `/ai-insights` | `POST` | `{ original_text, translated_text, src_lang, target_lang }` | Generates grammar structure analysis and vocabulary spotlights |
| `/chat` | `POST` | `{ original_text, translated_text, src_lang, target_lang, question, chat_history }` | Converses with Fluent Flow AI language tutor |
| `/tts` | `POST` | `{ text, lang }` | Synthesizes target speech output, generating local `.mp3` cache |

---

## 🎨 Theme Architecture Showcase

```
     [ Theme Switcher Clicked ]
                 │
                 ▼
     [ Body toggles .light-theme ] ──► Updates HSL custom variables
                 │
                 ▼
     [ localStorage.setItem() ] ────► Persists theme choice on reload
```

---

## 🤝 Contributing

Contributions are highly welcome! Please fork this repository, make your additions, and open a Pull Request. Make sure to adhere to modern clean-code guidelines, document your OOP service layers, and verify compile syntax check lists before submission.

---

## 📄 License

This project is licensed under the MIT License. Developed with passion under Google DeepMind agent frameworks.
