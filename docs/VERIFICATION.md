# Verification record

Executed locally on Windows with project-local Python 3.13.2, Node 22.14.0,
React 19, Vite 6 and Playwright Chromium. Package versions are recorded in
`requirements-api.lock` (universal Python 3.11+ resolution) and `frontend/package-lock.json`.
Optional ML package versions are not locked; they must be resolved and evaluated
for the target hardware before enabling those services.

| Check | Observed result |
| --- | --- |
| Full Python suite | **26 passed**; no paid APIs or model downloads |
| Document/service tests after final table-order change | **7 passed** |
| React component suite | **3 passed** |
| Desktop/mobile Playwright suite | **4 passed**, including actual malicious model output rendered as text |
| Frontend production build | Passed; JS about 268 kB / 82 kB gzip, CSS about 29 kB / 7 kB gzip |
| Ruff on backend, tests, evaluation and legacy app | Passed |
| JavaScript syntax checks | Passed for legacy script and browser tests |
| Google GenAI adapter configuration | SDK client/timeout/retry schema construction passed without a network call |
| Docker Compose configuration | Passed with validation-only secret values, using `config --quiet` |
| Frontend Linux image | Normal Dockerfile build passed |
| Full-stack Linux image | Passed with exact pinned local Linux wheels; the normal package-index build hit Docker TLS timeouts |
| Live PostgreSQL HTTP integration | Passed through Nginx and through the standalone full-stack API image: accounts, auth, persistence, ownership, deletion, unavailable providers and usage |
| Native OCR | Tesseract/OpenCV synthetic English image smoke check passed inside the Linux image; not an accuracy benchmark |
| AWS infrastructure | ECS Express Mode/RDS foundation and service templates pass local cfn-lint; not provisioned or verified against an AWS account |
| Screenshots | Desktop 1440 px and mobile 390 px inspected; mobile tutor banner corrected; no horizontal overflow in translation-flow browser assertions |

Python's current Starlette TestClient emits a non-failing deprecation warning about
its httpx integration. Browser tests emit non-failing terminal color warnings.
Neither warning was suppressed or presented as a test failure.

Tests cover Argon2 password hashing, JWT expiry and authentication, input bounds,
cross-user isolation, translation history, vocabulary, preferences, account deletion,
session memory/restoration, retrieved-source ID filtering, unavailable providers,
retry/failover, deadline handling, segmentation boundaries, private document jobs
and downloads, real TXT/DOCX extraction/export/table reading order, image decoding
failure, mocked OCR/speech/TTS orchestration, rate limiting and usage summaries.
RAG tests use deterministic embeddings/index doubles to verify source loading,
thresholding and caching. They do not measure embedding quality.

Evaluation tests check metric math and JSON/Markdown/PNG export using explicitly
labelled exact-match fixtures. Fixture scores are **not model benchmark results**.
There is no measured BLEU/chrF/COMET/WER/CER baseline for a real provider in this
repository yet. Inference cost/latency improvements have not been claimed.

## Outstanding release checks

- The normal package-index API Docker build needs CI/cloud confirmation. It failed
  on repeated TLS handshake timeouts to `files.pythonhosted.org` inside Docker;
  the identical URL succeeded on Windows. A verification copy of the Dockerfile
  replaced only dependency installation with a local wheel mount and used the
  same lockfile. No application behavior or dependencies were substituted.
- Native Tesseract executable is absent on the tested Windows host. Container
  English smoke extraction passed; multilingual OCR accuracy is still unmeasured.
- faster-whisper, NLLB, Sentence Transformer model downloads and COMET checkpoint
  execution were not performed. Success paths are deterministic adapter/pipeline
  tests, not evidence of real model accuracy or target-hardware capacity.
- Gemini/gTTS/Deep Translator live network behavior and current API-key access are
  unverified. Configuration flags indicate setup, never a successful provider probe.
- Load tests, managed backups/restoration, TLS ingress, observability delivery and
  cloud rollout require the selected production account, domain and operational setup.
- The original local `.git` metadata is incomplete and was left intact. Publication
  uses a clean clone of the existing GitHub repository, preserving upstream files
  absent from the supplied workspace. GitHub authentication was verified successfully
  with network access; the earlier sandboxed authentication check was misleading.
  No authenticated VibeNest connector was available. Its single-container configuration
  and dashboard procedure are prepared in `deployment/VIBENEST.md`; cloud deployment
  remains pending authenticated platform access and secret configuration.

This is a tested local implementation and deployment foundation, not a claim of a
fully production-validated deployment. See `docs/ROADMAP.md` for release gates and
`deployment/README.md` for the operational procedure.
