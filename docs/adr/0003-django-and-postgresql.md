# 0003. Python, Django 5.2 LTS and PostgreSQL

- Status: Proposed – awaiting developer review
- Date: 2026-09-28

## Context

We need auth, an admin panel for moderation, forms, server-rendered SEO pages and a relational
model, delivered quickly. The supervising developer is strongest in Python (some Java/Spring
Boot).

## Decision

- **Python 3.13 + Django 5.2 LTS** (security support until April 2028). Django gives an admin
  (our moderation tool), ORM + migrations, forms, auth, sitemaps and i18n out of the box, with a
  mature ecosystem (allauth, django-filter).
- **PostgreSQL 17** in every environment, including tests (no SQLite in tests, so constraints and
  query behaviour match production). Future needs are covered by Postgres itself: full-text
  search with Polish dictionaries, range types/exclusion constraints for the room calendar
  (Phase 2), JSONB.

Alternatives considered: Spring Boot (slower to build CRUD + admin, no built-in admin), FastAPI
(API-first; we would have to build admin, forms and templates ourselves), Rails/Laravel (outside
the team's skills).

## Consequences

- Very fast CRUD/admin development; one language across the codebase.
- Django's synchronous request model is fine for this workload; async can come later if needed.
- Upgrade path: Django 6.x LTS (2028) before 5.2 support ends.
