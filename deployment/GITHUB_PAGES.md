# GitHub Pages frontend hosting

The public frontend is built for:
https://pruthvi226.github.io/Translator-Project-OOPS/

The `pages.yml` workflow builds React with the repository's Vite base path and
publishes `frontend/dist`. GitHub Pages must use the GitHub Actions publishing
source. Pushes to `master` that change the frontend/workflow redeploy it; manual
workflow dispatch is also supported.

## Browser-only mode (default)

With `VITE_STATIC_ONLY=true` and no API URL, the site runs entirely as a static app.
No Render or AWS resources are needed.

- Text translation calls MyMemory directly over HTTPS. Select the actual source
  language; automatic detection and AI tone rewriting are unavailable. The UI
  limits requests to 5,000 characters and chunks them below 500 UTF-8 bytes.
  MyMemory imposes a daily quota; quota/network failures are reported and can be retried.
  Public translation memories can contain inaccurate entries; review important text.
- Image OCR uses Tesseract.js on the device. Its worker, WebAssembly engine and
  language models download from public CDNs on first use. Only extracted text,
  not the image itself, is sent to MyMemory.
- TXT, DOCX and text-based PDF extraction happens on-device with Mammoth and PDF.js.
  Files are limited to 10 MB; PDFs to 50 pages; extracted text to 5,000 characters.
  Scanned PDFs need pages uploaded as images. Translations download as UTF-8 TXT.
- Voice uses the browser's speech recognition rather than uploaded audio files.
  Browser/device support and microphone permission are required; recognition may
  use the browser vendor's online service. Speech playback requires an installed
  voice for the target language.
- Up to 100 translations and 100 vocabulary entries are stored in localStorage.
  They are device-local, not encrypted account storage or cloud backups. Settings
  includes a button to erase them. No credentials or AI keys are requested.
- AI tutoring and account controls are omitted in this mode. Normal local/Docker
  builds and explicitly configured API deployments retain authenticated features.

Run `cd frontend`, `npm ci`, `npm test` and `npm run test:browser` to verify the
static build. The browser tests use mocked provider responses for repeatability;
a live English-to-Hindi translation and actual OCR/PDF/DOCX extraction were also
verified in Chromium during deployment.

To connect a separately hosted backend:

1. Configure a working HTTPS FastAPI deployment.
2. Add `https://pruthvi226.github.io` to its `CORS_ORIGINS` (origin only, no repository
   path). Keep other required origins in the comma-separated list.
3. Set the repository Actions variable `VITE_API_BASE_URL` to the backend HTTPS
   origin, for example `https://translation-api.example.com`, without `/api/v1`.
4. Run the Pages workflow again. Vite embeds the backend's public URL in the bundle.
   Never put API keys, JWT secrets or database passwords in any `VITE_*` variable.

With an API URL set, the frontend uses the authenticated backend instead of
browser-only mode. Normal Docker/local builds keep same-origin API requests
unless `VITE_API_BASE_URL` is explicitly set.

No AWS resources are required or created by this workflow. GitHub Pages hosting
for this public repository is available with GitHub Free; model/backend services
have their own hosting and usage terms.

References: [GitHub Pages static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
and [Vite GitHub Pages configuration](https://vite.dev/guide/static-deploy.html#github-pages).

Browser provider: [MyMemory API](https://mymemory.translated.net/doc/spec.php), [usage limits](https://mymemory.translated.net/doc/usagelimits.php).
