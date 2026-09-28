# 0017. Free public demo uses SQLite

- Status: Accepted (2026-09-28)
- Date: 2026-09-28

## Context

The owner needs a URL three people can open and click through (home, listings, a listing,
signup, profiles) before the paid launch. The product itself stays on PostgreSQL (ADR 0003):
the rate limiter and the test suite depend on it, and `render.yaml` is the later Frankfurt
blueprint (web Starter, cron, Postgres Basic 256 MB). That blueprint must not be what the
demo deploys.

Render's free web service can build a Dockerfile. It has no persistent disk and spins down
when idle, so a paid database is not required for this temporary demo.

## Decision

- Keep `render.yaml` unchanged. Add `render.demo.yaml`: one web service, `plan: free`,
  Docker, no database and no cron.
- `config.settings.demo` forces SQLite and `DEMO_MODE`. It ignores any `DATABASE_URL`.
  Production settings are unchanged and do not ask for a preview password.
- On every demo process start, `prepare_demo` migrates, loads reference data and the fake
  Polish samples (including a Kraków job, a Wrocław room, a specialist and a clinic).
- Every page shows a banner that this is a demo and the data is made up.
- Sample accounts use `@example.com`. The public demo does not seed a superuser.

## Consequences

- The demo URL can run without a Render Postgres bill. Data disappears when the free
  instance spins down or redeploys, then the fake samples are created again.
- Signup on that URL still stores whatever email a visitor types. The demo is not a place
  for real personal data.
- The shared rate-limit upsert runs on SQLite in this mode only. Production counters stay
  in PostgreSQL (ADR 0014).
