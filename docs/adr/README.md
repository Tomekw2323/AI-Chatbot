# Architecture Decision Records

Short records of significant decisions, in the format of
[Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
All decisions below were made to start the project quickly and are **open for review by the
supervising developer**: to change one, add a new ADR that supersedes it (do not rewrite history).

| # | Decision | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-modular-monolith.md) | Modular monolith, not microservices | Proposed – awaiting developer review |
| [0003](0003-django-and-postgresql.md) | Python, Django 5.2 LTS and PostgreSQL | Proposed – awaiting developer review |
| [0004](0004-server-rendered-html-htmx-tailwind.md) | Server-rendered HTML with HTMX and Tailwind | Proposed – awaiting developer review |
| [0005](0005-polish-only-ui-i18n-ready.md) | Polish-only UI, i18n-ready | Proposed – awaiting developer review |
| [0006](0006-single-listing-table.md) | One `Listing` table for all listing kinds | Proposed – awaiting developer review |
| [0007](0007-single-account-type-organizations.md) | One account type; organizations with memberships | Proposed – awaiting developer review |
| [0008](0008-authentication-django-allauth.md) | Authentication with django-allauth (email + Google) | Proposed – awaiting developer review |
| [0009](0009-gdpr-eu-hosting-no-health-data.md) | GDPR: EU hosting, no health data before Phase 3 | Proposed – awaiting developer review |
| [0010](0010-tooling.md) | Tooling: uv, ruff, mypy, pytest, import-linter, pre-commit | Proposed – awaiting developer review |
| [0011](0011-hosting-render-frankfurt.md) | Hosting on Render (Frankfurt) | Proposed – awaiting developer review |

Template for new records: copy [template.md](template.md).
