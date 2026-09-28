# 0004. Server-rendered HTML with HTMX and Tailwind

- Status: Accepted (2026-09-28, decided by the technical lead on behalf of the owner; the supervising developer may supersede it)
- Date: 2026-09-28

## Context

Acquisition will rely heavily on search engines ("gabinet do wynajęcia Wrocław", "praca
psycholog Kraków"). Pages must be crawlable and fast. The team has no dedicated frontend
developer.

## Decision

- **Django templates** render all pages on the server. SEO landing pages per kind and city
  (`/ogloszenia/<kind>/<city>/`), canonical links, sitemap.
- **HTMX 2** (vendored in `static/vendor/`) for small interactive parts: filters swap the result
  list without a full reload (`hx-get`, partial templates prefixed with `_`). Every view works
  without JavaScript.
- **Tailwind CSS 4** compiled with the standalone CLI via `django-tailwind-cli` (no Node.js in
  the toolchain). Shared component classes (`btn-primary`, `card`...) and base form styles live
  in `assets/css/source.css`.

Alternative considered: SPA (React/Next.js) + API. Rejected for the MVP: two codebases, an API
layer, SSR setup for SEO and more build tooling, with no user-facing benefit for a listing board.

## Consequences

- One codebase, fast pages, good SEO by default.
- Rich interactions (e.g. a drag-to-book room calendar in Phase 2) may need a small JS island
  (e.g. Alpine.js or a single web component); that does not require changing this decision.
- A future mobile app would need a JSON API (Django REST Framework or django-ninja) on top of
  the same `services.py` layer.
