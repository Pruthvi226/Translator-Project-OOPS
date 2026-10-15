# Deploy FluentFlow AI on VibeNest

Target confirmed by the user: https://vibenest.net/.

VibeNest documents GitHub-connected Dockerfile deployment, managed PostgreSQL,
encrypted environment variables and an HTTPS platform address. See its
[official deployment flow](https://vibenest.net/how-it-works) and
[current platform overview](https://vibenest.net/). The current overview says
self-service custom domains are not yet available; use the assigned platform
address unless your account has another supported option. No custom domain or
undocumented deployment API is assumed here.

## Repository configuration prepared

Use the **repository root Dockerfile** and its default `standalone` target. It
builds React, installs the FastAPI service and Tesseract, and serves both the UI
and `/api/v1` from one HTTP origin. No separate Nginx service or Compose support
is required on VibeNest. The entrypoint binds `0.0.0.0` and honors `PORT` (8000
when unset). The Docker health check honors the same port. Keep one worker and
one application instance because document jobs are currently in-process.

The multi-service local Compose file explicitly selects Docker's `api` stage;
this does not change the default full-stack image used by VibeNest.

## Deployment procedure

1. Use `https://github.com/Pruthvi226/Translator-Project-OOPS`, branch `master`,
   with the reviewed FluentFlow upgrade and its root `backend/` and `frontend/`.
   Publication uses a clean checkout because the supplied local Git metadata is
   incomplete; existing upstream files are preserved.
2. Sign into your VibeNest account, create/select the project and attach that
   repository/branch. Choose Dockerfile build at the repository root. Do not use
   the old Flask start command or point the build to `AI-Translator-Pro`.
3. Provision/attach managed PostgreSQL using the account dashboard. Put its supplied
   connection URL in `DATABASE_URL`. `postgres://` and `postgresql://` are normalized
   to the installed psycopg driver. Preserve any required TLS query parameters.
4. Set secrets in VibeNest's encrypted environment-variable interface:

   ```dotenv
   ENVIRONMENT=production
   DATABASE_URL=<managed PostgreSQL connection URL>
   JWT_SECRET=<random stable secret of at least 32 characters>
   GEMINI_API_KEY=<your API key>
   GEMINI_MODEL=gemini-3.5-flash-lite
   PROVIDER_ORDER=gemini
   ENABLE_NLLB=false
   ENABLE_SPEECH=false
   ENABLE_RAG=false
   ENABLE_DEEP_TRANSLATOR=false
   RETENTION_DAYS=30
   ```

   Leave `FRONTEND_DIST` at the image default `/app/frontend-dist`. Keep optional
   local models disabled until packages, model storage and sufficient measured
   CPU/RAM capacity are provisioned. The advertised smallest server must not be
   assumed sufficient for multimodal model inference. Do not send secrets in chat
   or commit them to the repository.
5. If the dashboard requests an application port, use 8000 or the platform-assigned
   `PORT`. Set the health path to `/health/live`. After startup, also inspect
   `/health/ready`; it checks database access and provider configuration, not whether
   your API key can successfully call the configured model.
6. Deploy and verify the assigned HTTPS URL. Create a test account, make an actual
   translation and tutor call, upload a readable image and a TXT/DOCX document,
   and confirm private history/download access with a second account. Record
   resource usage, latency and API availability before treating the release as live.
7. Apply ingress limits, backup/restore policy, logs/alerts and provider cost budgets
   from the general [runbook](README.md). Record the deployed Git SHA, image digest
   and assigned URL for rollback. Do not assert a deployment without a successful
   platform result and an HTTP smoke test.

## Access boundary

No VibeNest connector was available in the plugin catalog during this session.
Its public setup page is not an authenticated deployment session. Account login,
project selection and secret entry remain necessary. The repository configuration
is prepared; no VibeNest deployment or domain assignment is claimed here.
