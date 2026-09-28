"""Production settings. Requires HTTPS termination in front of the app."""

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import env

DEBUG = False

SECRET_KEY = env("DJANGO_SECRET_KEY")
if len(SECRET_KEY) < 50 or SECRET_KEY.startswith("change-me"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be a random string of 50+ characters.")

ADMIN_URL = env("DJANGO_ADMIN_URL")
if ADMIN_URL.strip("/") in {"admin", ""} or not ADMIN_URL.endswith("/"):
    raise ImproperlyConfigured("Set DJANGO_ADMIN_URL to an unguessable path ending in '/'.")
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=1)
ALLAUTH_TRUSTED_PROXY_COUNT = TRUSTED_PROXY_COUNT
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 365)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# Preload is hard to undo; enable only once the final domain and HTTPS setup are stable.
SECURE_HSTS_PRELOAD = env.bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
if not SECURE_HSTS_PRELOAD:
    SILENCED_SYSTEM_CHECKS = ["security.W021"]
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_NAME = "__Host-sessionid"
CSRF_COOKIE_NAME = "__Host-csrftoken"
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

ADMINS = [("Admin", email) for email in env.list("DJANGO_ADMIN_EMAILS", default=[])]
