# FluentFlow AI implementation audit and roadmap

## Baseline inspected

The checkout contains `app.py`, `templates/index.html`, `static/script.js`,
`static/style.css`, root Docker configuration and requirements, and an
`AI-Translator-Pro/README.md`. The latter describes React/FastAPI/MongoDB code
that is absent. There are no tests or model evaluation data. The local `.git`
metadata is incomplete (`git status` fails); do not reconstruct it or overwrite
the user's metadata. The public GitHub repository was inspected read-only.
Existing `.env` contents were deliberately not read.

Working baseline: Flask text translation, Gemini insights/chat, browser dictation,
gTTS, language selection and theme switch. Risks: deprecated Google SDK/model,
unbounded inputs and provider calls, exposed exception text, model HTML inserted
without escaping, debug mode, unauthenticated endpoints, public audio persistence,
no account isolation, no readiness checks, no measured benchmarks. Startup model
construction was incorrectly described as connectivity verification. Docker excluded
the proposed replacement folder entirely. No OCR/document/server speech pipeline
existed. The README claimed features and assets that were not present.

## Delivery order

1. **Foundation** — preserve the Flask UI; build modular FastAPI schemas,
   PostgreSQL persistence (SQLite for development/tests), JWT/Argon2 auth,
   ownership checks, bounded requests, safe errors, health/readiness.
2. **AI services** — Google GenAI structured output, opt-in Deep Translator and
   NLLB adapters, segmentation, retries/failover, usage records, contextual tutor
   and optional source-filtered semantic RAG. Tests use injected providers only.
3. **Multimodal** — bounded uploads, decoded image validation and OCR preprocessing,
   lazy faster-whisper, gTTS bytes, background document jobs and private downloads.
4. **Product** — React/Tailwind workspace, voice/image/document modes, history,
   vocabulary, tutor, settings, themes and honest evaluation state.
5. **Verification and operations** — deterministic integration/component/E2E tests,
   evaluation CLI and charts, container builds/CI, deployment/runbook and limitations.

## Release gates

Passing deterministic tests does not certify translation quality. Before a public
release: run licensed, held-out multilingual data through each real configured
provider; validate OCR/speech on representative files and installed language packs;
test PostgreSQL backups and restoration; configure TLS, secrets, edge rate limits,
cost budgets and monitoring. Load-test one worker; move jobs to a durable queue
before adding workers/replicas. No cloud deployment or benchmark is claimed until
verified. All remaining limits are recorded in README.md.
