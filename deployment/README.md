# Production deployment runbook

The repository is prepared for a single-instance Linux VM/container host with
Docker Compose, PostgreSQL and a TLS ingress. No cloud resources are created by
the local setup. Choose the account, region, budget and domain before provisioning.

The active target is AWS. See [the AWS deployment templates and guide](aws/README.md).
The earlier [VibeNest guide](VIBENEST.md) remains available as an alternative;
the Compose procedure below supports local development and self-managed hosts.

1. Run CI and review `docs/VERIFICATION.md`. Set a stable secret, a URL-safe database
   password and provider key using your cloud secret manager. Never copy a developer
   `.env` into a container image. Set `ENVIRONMENT=production` and an explicit
   PostgreSQL URL. Do not use a default or generated-on-each-boot JWT secret.
2. Check out the reviewed revision on the selected Linux host and create a restricted
   `.env` (`chmod 600 .env`). Run `docker compose up --build -d`. Keep database/API
   ports private. The supplied web port binds only to host loopback.
3. Terminate TLS at the host ingress. Example Caddy host configuration:

   ```caddyfile
   translate.example.com {
       reverse_proxy 127.0.0.1:8080
   }
   ```

   Replace the example domain and point DNS to the host. Allow inbound 80/443 only
   for the ingress; restrict SSH administration. Set secure HTTP headers/HSTS after
   confirming all required hostnames work over HTTPS. Configure real-client rate
   limits at the ingress; tune the backend aggregate limiter for expected traffic.
4. Verify `/health/live` and `/health/ready` through the domain. Readiness checks
   configured providers and the database, not live API credentials. Make a real
   translation and tutor request, an image with installed OCR language, a document
   job and its private download, then verify a second account cannot access them.
   Test actual model availability, credentials and errors before opening access.
5. Run held-out evaluation and load tests. Set provider cost rates/budgets and alerts
   for P95 latency, 5xx/503/429 rates and failed document jobs. Do not log user text,
   passwords, authorization headers or secret values. Monitor container resource
   usage and ship sanitized JSON application logs to your chosen log system.
6. Configure encrypted PostgreSQL backups using managed backups or `pg_dump` under
   an operations account. Test restore to a separate database before launch. Record
   RPO/RTO, retention and deletion behavior of backups. Do not put backup files in Git.
7. Use immutable image/revision tags for releases. Back up first; use reviewed schema
   migrations when schema changes begin. Roll back images to a previous known good
   SHA; restore data only using an approved recovery procedure. Startup intentionally
   marks interrupted in-process jobs failed. Keep one API worker/replica until a
   durable queue and distributed limits replace the current job runtime.

CI validates builds. `.github/workflows/publish.yml` publishes SHA-tagged images only
when manually invoked; it does not deploy or configure a cloud account. Add a protected
deployment environment and host-specific rollout only after selecting that host.

Local verification started the initially stopped Docker engine. The frontend
image built normally; the full-stack API image built using pinned local Linux
wheels because Docker's TLS connections to the Python package host timed out.
Both the Nginx and standalone HTTP paths passed isolated PostgreSQL account/privacy
smoke tests. A synthetic English image passed native Tesseract/OpenCV extraction
inside the image. No real model quality benchmark or cloud rollout is claimed.

For an isolated smoke test after building images with the tags used in CI:

```sh
docker compose -p fluentflow-verification -f deployment/compose.verify.yml up -d --wait
python -m tests.smoke_deployment
docker compose -p fluentflow-verification -f deployment/compose.verify.yml down
```

This uses dummy test credentials, no provider key and an ephemeral database. Never
use the verification Compose file for production. The standalone test path is
http://127.0.0.1:18081; Nginx is http://127.0.0.1:18080.
