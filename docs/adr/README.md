# Architecture Decision Records

Short records of significant decisions, in the format of
[Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
The owner delegated technical decisions; the initial set was accepted by the technical lead on
2026-09-28. The supervising developer can challenge any of them: add a new ADR that supersedes
the old one (do not rewrite history).

| # | Decision | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-modular-monolith.md) | Modular monolith, not microservices | Accepted |
| [0003](0003-django-and-postgresql.md) | Python, Django 5.2 LTS and PostgreSQL | Accepted |
| [0004](0004-server-rendered-html-htmx-tailwind.md) | Server-rendered HTML with HTMX and Tailwind | Accepted |
| [0005](0005-polish-only-ui-i18n-ready.md) | Polish-only UI, i18n-ready, Polish msgids | Accepted |
| [0006](0006-single-listing-table.md) | One `Listing` table for all listing kinds | Accepted |
| [0007](0007-single-account-type-organizations.md) | One account type; organizations with memberships | Accepted |
| [0008](0008-authentication-django-allauth.md) | Authentication with django-allauth (email + Google) | Accepted |
| [0009](0009-gdpr-eu-hosting-no-health-data.md) | GDPR: EU hosting, no health data before Phase 3 | Accepted |
| [0010](0010-tooling.md) | Tooling: uv, ruff, mypy, pytest, import-linter, pre-commit | Accepted |
| [0011](0011-hosting-render-frankfurt.md) | Hosting on Render (Frankfurt) | Accepted |
| [0012](0012-moderation-and-posting-rules.md) | Publish immediately, moderate afterwards, abuse controls | Accepted |
| [0013](0013-guest-contact-with-turnstile.md) | Guest contact only through Cloudflare Turnstile | Accepted |
| [0014](0014-rate-limiting-in-postgresql.md) | Rate limiting stored in PostgreSQL | Accepted |
| [0015](0015-http-security-hardening.md) | HTTP security hardening: CSP, headers, cookies, admin path | Accepted |
| [0016](0016-gdpr-self-service-and-retention.md) | GDPR self-service: export, deletion, retention, no tracking | Accepted |

Template for new records: copy [template.md](template.md).
