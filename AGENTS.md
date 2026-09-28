# AGENTS.md

Read `SCOPE.md` first, then follow its links. This file stays the short always-on rule file
for agents and humans changing code. It is not a second copy of the guide.
Cursor-specific rules live in `.cursor/rules/*.mdc` and mirror this file.

## Product in one paragraph

Polish-language platform for the mental-health industry. MVP: job/internship/volunteering board
(+ "looking for work" posts by specialists), hourly/daily therapy-room rental listings, and
profile pages for specialists and organizations. Patient booking is Phase 3: do **not** build
patient features or store health data without an explicit task and an ADR.

## Commands (run before you finish)

```bash
uv run ruff format . && uv run ruff check .   # format + lint
uv run mypy .                                  # types
uv run lint-imports                            # module boundaries
uv run python manage.py makemigrations --check --dry-run
uv run pytest --cov                            # needs Postgres; fails below the coverage floor
```

All five must pass. CI runs the same, plus `pip-audit`.

## Architecture rules (hard)

- Modular monolith. Apps and allowed import direction:
  `privacy` → `listings` → `profiles | organizations` → `accounts` → `core`.
  `profiles` and `organizations` never import each other. Enforced by import-linter.
- Cross-app calls go through the lower app's `services.py` (e.g.
  `organizations.services.can_manage_organization`). Do not query another app's internals.
- Lower apps showing higher-app data do it via template tags of the higher app
  (`listings/templatetags/listing_tags.py`), never via Python imports.
- Views stay thin: permissions in `permissions.py`/`services.py`, multi-step logic in
  `services.py`, invariants in `models.py` (`clean()` + DB constraints).
- New significant decisions need an ADR in `docs/adr/` (copy `template.md`).

## Django conventions

- Custom user: always `settings.AUTH_USER_MODEL` in FKs, `apps.accounts.models.User` in code.
- In views that require login use `apps.accounts.services.require_user(request)` to get a typed
  `User` (no `assert`).
- Public querysets: use `.public()` managers (`Listing.objects.public()`,
  `SpecialistProfile.objects.public()`, `Organization.objects.public()`), never re-implement
  visibility rules.
- Listing status changes only via `Listing.publish()/archive()/expire()`.
- Choices: `TextChoices` with English values and Polish labels.
- Slugs: `apps.core.text.slugify_pl` / `unique_slug` (handles "ł").
- Every model change: migration in the same commit + update `docs/domain-model.md`.
- Reference data changes: edit `apps/core/fixtures/reference_data.json` (keep pks stable).

## Language

- Code, identifiers, comments, commits, developer docs: **English**.
- User-facing strings: **Polish**, always wrapped: `gettext_lazy as _` in Python,
  `{% translate %}` / `{% blocktranslate %}` in templates (ADR 0005).
- URLs are Polish (`/ogloszenia/`, `/specjalisci/`, `/organizacje/`, `/panel/`).
- Comments explain *why* (constraints, trade-offs), never narrate *what* the code does.

## Frontend

- Server-rendered Django templates, Tailwind utility classes, shared components in
  `assets/css/source.css` (`btn-primary`, `btn-secondary`, `card`, `badge`, `link`).
- HTMX for partial updates; partial templates start with `_`; pages must work without JS.
- Forms render via `{{ field.as_field_group }}` or `includes/form_fields.html`.
- No Node.js/npm. Tailwind is built by `python manage.py tailwind build`.

## Tests

- pytest + factory_boy, tests in `apps/<app>/tests/test_*.py`, factories in
  `apps/<app>/tests/factories.py`. Use `Factory.create(...)` / `.build(...)` (typed).
- Every permission rule needs an allowed **and** a denied test. Every new filter needs a test.
- Tests run on PostgreSQL, never SQLite.

## Security and GDPR (read docs/security.md)

- Every view that changes data: `require_POST`, an object-level permission check
  (403 for edit actions, 404 for invisible objects), and a test for allowed **and** denied users.
- Publishing or contacting requires a verified email: `allauth.account.decorators.verified_email_required`.
- Abuse-prone POSTs get `@ratelimit("<scope>")` from `apps.core.ratelimit` with the rate in
  `settings.RATE_LIMITS`, plus a test that the limit returns 429.
- Never use `|safe`, `mark_safe` or `{% autoescape off %}` in HTML templates (a test enforces it).
  User content is plain text. Redirect targets from input go through `url_has_allowed_host_and_scheme`.
- No inline `<script>` or `on*=` handlers: the CSP blocks them. New external origins must be added
  to `CONTENT_SECURITY_POLICY` deliberately.
- Forms list fields explicitly; never expose moderation or ownership fields.
- New personal data: include it in `apps/privacy/services.py` export and deletion, with tests.
- No secrets in code; configuration via environment variables (`.env.example` documents them).
- Do not log personal data (emails, messages). No health data in the MVP.
- Anything that stores new personal data: note it in the PR and consider retention.

## Git

Conventional Commits (`feat(listings): ...`), small PRs against `main`, see CONTRIBUTING.md.
