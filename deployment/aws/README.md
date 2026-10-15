# FluentFlow AI on AWS

**Status: templates prepared and validated locally; no AWS resources deployed.**
The active deployment target is AWS. Account sign-in, region and spending limit
must be supplied before provisioning. No account credentials were configured on
the development machine when this work began. Never paste access keys into chat.

## Prepared architecture

- Root Dockerfile builds the React/FastAPI application as one Linux image.
- ECR stores immutable revision-tagged images with scan-on-push enabled.
- ECS Express Mode runs one 0.5-vCPU/2-GB task and provides a managed HTTPS endpoint.
- PostgreSQL runs in encrypted RDS storage in two private subnets. Only tasks with
  the application database security group can reach port 5432.
- Application tasks use public subnets for outbound Gemini access, with inbound
  access controlled by the Express-managed load-balancer/task security groups.
  The additional database identity security group adds no inbound rules. No NAT
  gateway is provisioned by these templates.
- Secrets Manager holds a generated database password, connection URL and JWT
  secret, plus the supplied Gemini key. The task execution role can read only the
  three application secrets. No secret values appear in stack outputs.
- CloudWatch application logs retain 14 days. Database backups retain seven days.
  RDS deletion protection is enabled; deletion/replacement requests retain snapshots.

`foundation.yaml` creates the network, database, secrets, ECR and roles.
`service.yaml` deploys a pushed image using exported foundation resources. This
two-step flow ensures the image exists before ECS attempts to start it.

This is a single-task starter configuration, not a high-availability application
deployment. Multi-AZ RDS is an explicit foundation parameter. Local speech/RAG/NLLB
models remain disabled. Add a durable job queue before increasing replica counts.

AWS [documents ECS Express Mode](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-overview.html)
and its [network defaults](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/express-service-work.html).
App Runner is not used: AWS stopped accepting new App Runner customers on April 30,
2026; see [the availability change](https://docs.aws.amazon.com/apprunner/latest/dg/apprunner-availability-change.html).

## Authenticate and review costs first

Install the official [AWS CLI v2](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).
Use `aws login --profile fluentflow` for browser-based console sign-in, or
`aws configure sso --profile fluentflow` followed by `aws sso login --profile fluentflow`
for IAM Identity Center. Use a deployment role/IAM identity rather than root.
See [AWS browser login](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html).

Verify the target account with `aws sts get-caller-identity --profile fluentflow`.
Specify the selected region explicitly on every provisioning command. Review the
account/region-specific estimate before execution: Fargate, ALB/LCUs, public IPv4,
RDS compute/storage/backups, Secrets Manager, ECR, Container Insights/logs, and data
transfer all have separate charges. The single-task cap is not a spending cap.
Create budget alerts; alerts do not stop resources or guarantee a billing ceiling.
No free-tier eligibility or unmeasured monthly price is assumed.

## Validate and deploy

```sh
pip install -r requirements-aws.txt
cfn-lint deployment/aws/foundation.yaml deployment/aws/service.yaml
```

1. Create a CloudFormation change set from `foundation.yaml` in the selected region
   with stack name `fluentflow-foundation`. Review the IAM and billable resources.
   Supply `GeminiApiKey` through the console's masked parameter field or an SDK call
   that keeps its value in memory; do not put it in shell arguments, Git or logs.
   The stack needs `CAPABILITY_IAM`. Execute after the account/budget are confirmed.
2. Wait for `CREATE_COMPLETE`. Obtain `RepositoryUri` from the stack outputs and
   authenticate Docker to that registry using ECR's login password through stdin.
   Build the default standalone Docker target for `linux/amd64` and push an
   immutable tag corresponding to the reviewed Git commit. ECR rejects reused tags.
   The repository is private; the ECS execution role pulls it without public access.
3. Create/review a change set from `service.yaml`, passing `FoundationStack` and
   `ImageUri`. Execute it and wait for the service to stabilize. The `Endpoint`
   output gives the assigned HTTPS address; a custom domain is not required.
4. Verify the UI, `/health/live` and `/health/ready` at the real HTTPS endpoint.
   Readiness checks provider configuration, not API-key validity. Create a test
   account, make a real translation/tutor call, test OCR/document translation and
   a private download, then verify isolation with another account. Do not report
   success without checking the actual deployed revision and endpoint.
5. For later releases, push a new SHA tag and update `ImageUri` using a change set.
   Keep a previous working tag for rollback. Deployments/restarts may fail active
   in-process document jobs; do not scale out until a queue owns job execution.

## Operational limits

- The initial database owner is used for schema bootstrap. Before exposing real
  user data, create a database role limited to the application schema, update the
  connection-URL secret and redeploy. The database is not publicly reachable.
- Database transport uses `sslmode=require`; configure RDS CA trust and `verify-full`
  for certificate identity verification before a hardened production release.
- Generated credentials are stable across container restarts. Secret rotation must
  update the database and connection URL together and roll out new tasks; changing
  only one breaks authentication. Automatic rotation is not configured here.
- Express Mode's managed IAM infrastructure policy can manage supporting resources.
  Review its AWS-maintained permissions and use a restricted deployment identity.
- A public deployment additionally needs agreed retention/backup restoration tests,
  real-model validation, ingress rate-limit/load review and monitored cost budgets.
- Deleting the service does not delete the foundation. RDS deletion protection must
  be intentionally disabled before deleting its stack. Snapshots, secrets and ECR
  are retained to protect data and can continue incurring charges. Do not clean
  them up automatically without reviewing data retention and recovery needs.

Local CloudFormation validation checks schema and references. It does not prove
regional engine/class availability, quotas, permissions, pricing, or successful
live provisioning. These checks require the selected authenticated AWS account.
