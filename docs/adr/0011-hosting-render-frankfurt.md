# 0011. Hosting on Render (Frankfurt)

- Status: Proposed – awaiting developer review
- Date: 2026-09-28

## Context

We need cheap, low-maintenance hosting in the EU (ADR 0009) for one web process, one Postgres
database and a daily cron job, with HTTPS, deploys from GitHub and managed backups.

## Decision

Use **Render**, region **Frankfurt**, described as code in `render.yaml` (Blueprint):

- Web service from the `prod` stage of the `Dockerfile` (gunicorn, WhiteNoise), Starter plan.
- Managed PostgreSQL 17 (Basic 256 MB to start; daily backups).
- Cron job `manage.py expire_listings` daily.
- `preDeployCommand` runs migrations; reference data is loaded once at the first deploy.

Estimated cost at the start (verify current pricing): roughly 7 USD (web) + 6 USD (Postgres) +
~1 USD (cron) per month.

Alternatives: **Fly.io** (region `fra`/`ams`, comparable price, more ops knobs, Postgres is
self-managed or via a partner), **Railway** (EU West region, usage-based pricing, simple but less
predictable cost), a VPS at a Polish/EU provider (cheapest, but we would own patching, backups,
TLS). The Docker image is portable to any of them.

## Consequences

- Near-zero ops; deploy on merge to `main`.
- Render free Postgres expires, so the paid tier is required for real data.
- Uploaded media (Phase 1.5) will need EU object storage (e.g. S3-compatible in an EU region);
  Render disks are not shared between instances.
