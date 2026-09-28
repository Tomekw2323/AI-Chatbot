# config

Local contract. The map of every segment is `docs/segmenty.md`.

## Owns

- `config/settings/base.py` and overlays `dev.py`, `test.py`, `prod.py`, `demo.py`.
- `config/urls.py`: `urlpatterns`, `healthz`.
- `config/wsgi.py` and `config/asgi.py`: `application`.
- `config/sitemaps.py`: `sitemaps`.

## Must not

Apps do not import `config`. They read `django.conf.settings`. This package is outside the import-linter layers in `pyproject.toml`.

## Public surface

`DJANGO_SETTINGS_MODULE` is one of `config.settings.dev`, `config.settings.test`, `config.settings.prod`, `config.settings.demo`.

`config.wsgi:application` is the gunicorn entry (default module `config.settings.prod`). `config.asgi:application` is the ASGI entry. `config.urls.healthz` serves `healthz/`. `config.sitemaps.sitemaps` keys are `listings`, `profiles`, `organizations`, `landing`.

Mail is settings, not an app. `base.py` loads `EMAIL_URL` with `env.email_url` (default `consolemail://`). `demo.py` sets `EMAIL_BACKEND` to `django.core.mail.backends.console.EmailBackend`. `test.py` sets `django.core.mail.backends.locmem.EmailBackend`.

## Replace without editing apps

Switch `DJANGO_SETTINGS_MODULE` between `config.settings.prod` and `config.settings.demo`, or change `EMAIL_URL` / `EMAIL_BACKEND`. `render.yaml` and `render.demo.yaml` are the two deploy switches.

## How to test

pytest loads `config.settings.test`. These tests boot the other overlays:

```bash
uv run pytest apps/listings/tests/test_demo.py apps/core/tests/test_security.py
```
