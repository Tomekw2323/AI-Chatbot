# 0010. Tooling: uv, ruff, mypy, pytest, import-linter, pre-commit

- Status: Proposed – awaiting developer review
- Date: 2026-09-28

## Context

Code quality must stay high with a small team and AI agents contributing. The toolchain should be
fast and have few moving parts.

## Decision

- **uv** for Python version + dependency management (`pyproject.toml`, `uv.lock`), chosen over
  Poetry for speed and because it also installs Python itself.
- **ruff** for linting (pycodestyle, pyflakes, isort, bugbear, pyupgrade, django, bandit rules)
  and formatting (line length 100).
- **mypy** with **django-stubs**: `disallow_untyped_defs` and `check_untyped_defs` for app code,
  relaxed for tests; not full `--strict` (too noisy with Django generics for little gain).
- **pytest + pytest-django + factory_boy**, tests next to code (`apps/<app>/tests/`), always
  against PostgreSQL.
- **import-linter** enforces module layers (ADR 0002).
- **pre-commit** runs the same checks locally; **GitHub Actions** runs them in CI plus
  `check --deploy` with production settings and a production Docker build.

## Consequences

- One command per check, identical locally and in CI (pre-commit hooks call `uv run`, so tool
  versions come from `uv.lock`).
- Contributors need uv installed (one-line install) or can use Docker only.
