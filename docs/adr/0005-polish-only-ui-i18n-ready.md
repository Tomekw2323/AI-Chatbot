# 0005. Polish-only UI, i18n-ready

- Status: Accepted (2026-09-28, decided by the technical lead on behalf of the owner; the supervising developer may supersede it)
- Date: 2026-09-28

## Context

The market is Poland only; the UI is Polish. Other languages (Ukrainian, English for foreign
specialists) are plausible later. Code must be readable by any developer.

## Decision

- Code, identifiers, comments, commit messages and developer docs are in **English**.
- `LANGUAGE_CODE = "pl"`, `TIME_ZONE = "Europe/Warsaw"`. Every user-facing string is wrapped in
  gettext (`gettext_lazy` in Python, `{% translate %}` / `{% blocktranslate %}` in templates).
- **The source strings (msgids) are Polish.** This avoids maintaining an English→Polish `.po` file
  for a Polish-only product, while still allowing new languages by adding `locale/<lang>/` files.
- URL paths are Polish (`/ogloszenia/`, `/specjalisci/`) for SEO; enum values stored in the DB
  are English (`room_rental`), their labels Polish.

## Consequences

- No translation step during the MVP; third-party apps (Django, allauth) already ship Polish.
- If English becomes the primary language later, msgids would need converting (scriptable).
- Reviewed 2026-09-28: kept. English msgids would add a translation step to every UI change
  for a product with one market; the conversion cost later is bounded and scriptable.
- Translated URLs (`i18n_patterns`) are not used; add them only if a second language appears.
