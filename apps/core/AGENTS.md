# apps/core

Local contract. The map of every segment is `docs/segmenty.md`.

## Owns

Reference data and shared technical helpers: `TimeStampedModel`, `ReferenceModel`, `Voivodeship`, `City`, `Specialization`, `TherapyApproach`, `RateLimitCounter`, fixture `fixtures/reference_data.json`, Polish slugs, the Postgres rate-limit counter, Turnstile verification, `SecurityHeadersMiddleware`, context processor `site`.

## Must not import

Any other package under `apps`. This is the bottom layer.

## Public surface

- `apps.core.text.slugify_pl`, `unique_slug`
- `apps.core.ratelimit.ratelimit`, `check`, `hit`, `client_ip`, `rate_limited_response`, `purge_old_windows`, `parse_rate`
- `apps.core.captcha.is_enabled`, `verify` (`TOKEN_FIELD` is the form field name)
- `apps.core.middleware.SecurityHeadersMiddleware`
- `apps.core.context_processors.site`
- Models listed under Owns. Other apps reference them by foreign key; they do not copy visibility rules from here.

`daily_maintenance` in listings calls `purge_old_windows`.

## Replace without editing other apps

Turnstile keys and `RATE_LIMITS` live in settings. A replacement of this app has to keep the names above; higher apps import them directly.

## How to test

```bash
uv run pytest apps/core/tests
```
