# Contributing

## Setup

See the [README quickstart](README.md#quickstart-5-commands). Then install the git hooks once:

```bash
uv sync
uv run pre-commit install
```

## Branching

- `main` is always deployable. No direct pushes once the repository is shared; protect it with
  "require PR + passing CI".
- Work on short-lived branches from `main`:
  - `feat/<short-description>` – new functionality (`feat/room-calendar`)
  - `fix/<short-description>` – bug fixes
  - `chore/…`, `docs/…`, `refactor/…`, `test/…` – as the name says
- Rebase on `main` (or merge `main` in) before requesting review; keep branches small (ideally
  under ~400 changed lines excluding migrations and fixtures).

## Commits

[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <imperative summary, max ~72 chars>

<optional body: what and why, not how>
```

- `type`: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`
- `scope`: the app or area, e.g. `listings`, `profiles`, `organizations`, `core`, `accounts`,
  `deploy`, `ci`
- Examples: `feat(listings): add price sorting`, `fix(profiles): hide blocked profiles in sitemap`
- One logical change per commit. Migrations go in the same commit as the model change.
- Messages in English.

## Pull requests

1. Open a PR against `main` early (draft is fine). Fill in the template: what, why, how tested,
   screenshots for UI changes.
2. CI must be green: ruff (format + lint), mypy, import-linter, missing-migrations check,
   `check --deploy`, pytest on PostgreSQL, production Docker build.
3. At least one review by the supervising developer. AI-generated PRs get the same review.
4. Squash-merge with a Conventional Commit title; delete the branch.

### Review checklist

- [ ] Module boundaries respected (no imports "upwards", cross-app calls via `services.py`)
- [ ] Permissions checked in `permissions.py`/`services.py`, with tests for allowed and denied cases
- [ ] New user-facing strings wrapped in gettext, Polish source text
- [ ] Migrations included, reversible, and safe for existing data
- [ ] No personal data in logs; no secrets in code; GDPR impact considered for new data fields
- [ ] Significant decision? Add an ADR in `docs/adr/`
- [ ] Docs updated (`docs/domain-model.md` for model changes)

## Coding conventions

See [AGENTS.md](AGENTS.md) – it applies to humans too.
