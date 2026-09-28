"""Settings used by pytest (see ``[tool.pytest.ini_options]`` in pyproject.toml)."""

from .base import *  # noqa: F403

DEBUG = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
ACCOUNT_EMAIL_VERIFICATION = "optional"
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
TURNSTILE_SITE_KEY = ""
TURNSTILE_SECRET_KEY = ""
