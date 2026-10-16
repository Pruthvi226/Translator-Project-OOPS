# GitHub Pages frontend hosting

The public frontend is built for:
https://pruthvi226.github.io/Translator-Project-OOPS/

The `pages.yml` workflow builds React with the repository's Vite base path and
publishes `frontend/dist`. GitHub Pages must use the GitHub Actions publishing
source. Pushes to `master` that change the frontend/workflow redeploy it; manual
workflow dispatch is also supported.

GitHub Pages hosts static HTML, JavaScript and CSS. It does not run Flask,
FastAPI, PostgreSQL, OCR, speech models or server-side Gemini calls. Until an
API is connected, the published frontend explicitly shows that its translation
service is unavailable. It does not fake translations or send account passwords
to GitHub Pages. Themes, navigation and workspace exploration remain available.

To connect a separately hosted backend:

1. Configure a working HTTPS FastAPI deployment.
2. Add `https://pruthvi226.github.io` to its `CORS_ORIGINS` (origin only, no repository
   path). Keep other required origins in the comma-separated list.
3. Set the repository Actions variable `VITE_API_BASE_URL` to the backend HTTPS
   origin, for example `https://translation-api.example.com`, without `/api/v1`.
4. Run the Pages workflow again. Vite embeds the backend's public URL in the bundle.
   Never put API keys, JWT secrets or database passwords in any `VITE_*` variable.

With no API URL, `VITE_STATIC_ONLY=true` blocks API calls and the site clearly
reports the missing service. Normal Docker/local builds keep same-origin API
requests unless `VITE_API_BASE_URL` is explicitly set.

No AWS resources are required or created by this workflow. GitHub Pages hosting
for this public repository is available with GitHub Free; model/backend services
have their own hosting and usage terms.

References: [GitHub Pages static hosting](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
and [Vite GitHub Pages configuration](https://vite.dev/guide/static-deploy.html#github-pages).
