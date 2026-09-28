"""Public free demo. SQLite only — never the paid Postgres blueprint.

Selected with ``DJANGO_SETTINGS_MODULE=config.settings.demo``. The disk is
ephemeral on Render's free plan, so ``prepare_demo`` reloads fake data on
every process start. Production stays on ``config.settings.prod``.
"""

import os
import tempfile

# Force SQLite before base.py reads DATABASE_URL, so a copied production URL
# cannot point this mode at the paid database. The free instance disk is ephemeral.
_default_sqlite = os.path.join(tempfile.gettempdir(), "bartoszup-demo.sqlite3")
_sqlite_path = os.environ.get("DEMO_SQLITE_PATH", _default_sqlite)
os.environ["DATABASE_URL"] = "sqlite:///" + _sqlite_path

from .base import *  # noqa: E402, F403
from .base import env  # noqa: E402

DEMO_MODE = True
DEBUG = False

# One process, short-lived file. Persistent connections deadlock SQLite.
DATABASES["default"]["CONN_MAX_AGE"] = 0

_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")
if _render_host:
    if _render_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_render_host)
    _origin = f"https://{_render_host}"
    if _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)
    SITE_URL = _origin

# No inbox on the free demo: signup has to finish in the browser.
ACCOUNT_EMAIL_VERIFICATION = "optional"
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=60 * 60 * 24 * 365)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# The image collects static files with the prod manifest storage. Match it.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
