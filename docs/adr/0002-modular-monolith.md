# 0002. Modular monolith, not microservices

- Status: Proposed – awaiting developer review
- Date: 2026-09-28

## Context

BartoszUP is a new product with unvalidated scope, a very small team (one supervising developer
plus AI agents), no traffic yet and a priority on delivering fast. The supervising developer has
previously built a Spring Boot microservices system, so microservices are a natural reflex.

The MVP domain (users, organizations, profiles, listings, reference data) is small and highly
interconnected: nearly every page joins listings with cities, organizations and profiles, and
permission checks cross those areas.

## Decision

Build a **modular monolith**: one Django project, one deployable, one PostgreSQL database, split
into Django apps (`core`, `accounts`, `organizations`, `profiles`, `listings`) with **one-way
dependencies enforced by import-linter** in CI (see `docs/architecture.md`). Cross-module calls
go through each module's `services.py`.

Explicitly **not** microservices at this stage, because:

1. **No independent scaling or deployment need.** Load is tiny; one small instance handles it.
2. **Distributed-system tax.** Microservices would add service discovery, inter-service auth,
   network failures, retries, eventual consistency, distributed tracing, per-service CI/CD and
   databases, which is weeks of work that does not move the MVP forward.
3. **Transactions and joins.** Listing pages need data from 4 modules in one query; publishing an
   organization listing needs a permission check and a write in one transaction. In one database
   this is trivial and consistent.
4. **Unclear boundaries.** Boundaries drawn before product-market fit are usually wrong. Moving
   code between Django apps is a refactor; moving it between services is a migration project.
5. **Cost and operations.** One web service + one managed Postgres fits a ~15 EUR/month budget
   and one person's attention.

## Consequences

- Fast development, simple local setup (`docker compose up`), one CI pipeline, one deploy.
- Discipline is needed to keep modules decoupled; import-linter makes violations fail CI.
- If a module later needs isolation (most likely patient booking in Phase 3, because of GDPR
  art. 9 health data, or a payments integration), it can be extracted along an existing
  boundary, its `services.py` becoming an API. Revisit this ADR when: a module needs a different
  scaling profile, a separate team owns it, or compliance requires data isolation.
