"""Settings shared by every environment.

Environment-specific overrides live in ``dev.py``, ``test.py`` and ``prod.py``.
All secrets and deployment-specific values come from environment variables
(see ``.env.example``); nothing sensitive is hard-coded here.
"""

from pathlib import Path

import django_stubs_ext
import environ
from csp.constants import NONE, SELF, UNSAFE_INLINE
from django.utils.translation import gettext_lazy as _

# Makes generic classes such as ``ModelAdmin[Model]`` subscriptable at runtime.
django_stubs_ext.monkeypatch()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS: list[str] = env.list("DJANGO_ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS: list[str] = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

SITE_ID = 1
SITE_NAME = "BartoszUP"
SITE_URL = env("SITE_URL", default="http://localhost:8000")

# Public free demo (config.settings.demo). Production and local dev stay off.
DEMO_MODE = False

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
]
THIRD_PARTY_APPS = [
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django_filters",
    "django_htmx",
    "django_tailwind_cli",
    "csp",
]
# Order reflects the allowed dependency direction (see docs/architecture.md):
# an app may import only from apps listed *above* it.
LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.organizations",
    "apps.profiles",
    "apps.listings",
    "apps.privacy",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DATABASE_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Shared across workers/instances without extra infrastructure; used by allauth's
# rate limits. Created by ``manage.py createcachetable``.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}

# ---------------------------------------------------------------------------
# Authentication (django-allauth, email-only login + Google)
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LOGIN_URL = "account_login"
LOGIN_REDIRECT_URL = "dashboard"

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = env("ACCOUNT_EMAIL_VERIFICATION", default="mandatory")
ACCOUNT_SIGNUP_FORM_CLASS = "apps.accounts.forms.SignupForm"
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[BartoszUP] "
ACCOUNT_PREVENT_ENUMERATION = True
# Merged into allauth's defaults; tighter than defaults for signup and failed logins.
ACCOUNT_RATE_LIMITS = {
    "signup": "10/h/ip",
    "login_failed": "10/m/ip,5/15m/key",
    "reset_password": "10/h/ip,3/h/key",
}

SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_PROVIDERS: dict[str, dict[str, object]] = {
    "google": {"SCOPE": ["profile", "email"], "AUTH_PARAMS": {"access_type": "online"}},
}
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS["google"]["APPS"] = [
        {"client_id": GOOGLE_CLIENT_ID, "secret": GOOGLE_CLIENT_SECRET, "key": ""}
    ]

# ---------------------------------------------------------------------------
# Security (see docs/security.md)
# ---------------------------------------------------------------------------
# Admin lives at an unguessable path in production (DJANGO_ADMIN_URL, ADR 0015).
ADMIN_URL = env("DJANGO_ADMIN_URL", default="admin/")

# Number of reverse proxies in front of the app that append to X-Forwarded-For
# (Render: 1). 0 means "use REMOTE_ADDR". Wrong values let clients spoof their IP.
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=0)
ALLAUTH_TRUSTED_PROXY_COUNT = TRUSTED_PROXY_COUNT

# Application rate limits, "<count>/<period>/<user|ip>", see apps/core/ratelimit.py.
RATE_LIMITS = {
    "listing_create": "10/h/user,50/d/user",
    "inquiry": "10/h/user,30/h/ip",
    "inquiry_guest": "3/h/ip,10/d/ip",
    "listing_report": "10/h/user",
    "organization_create": "5/d/user",
    "data_export": "5/h/user",
}
LISTING_REPORTS_AUTO_FLAG = env.int("LISTING_REPORTS_AUTO_FLAG", default=3)
INQUIRY_RETENTION_DAYS = env.int("INQUIRY_RETENTION_DAYS", default=365)

# Cloudflare Turnstile protects guest forms; guest contact is disabled without keys.
TURNSTILE_SITE_KEY = env("TURNSTILE_SITE_KEY", default="")
TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY", default="")

CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
PERMISSIONS_POLICY = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"

TURNSTILE_ORIGIN = "https://challenges.cloudflare.com"
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF, TURNSTILE_ORIGIN],
        # Inline style attributes are used by Django admin; no inline scripts anywhere.
        "style-src": [SELF, UNSAFE_INLINE],
        "img-src": [SELF, "data:"],
        "font-src": [SELF],
        "connect-src": [SELF],
        "frame-src": [TURNSTILE_ORIGIN],
        "frame-ancestors": [NONE],
        "form-action": [SELF, "https://accounts.google.com"],
        "base-uri": [SELF],
        "object-src": [NONE],
    }
}

# No file uploads yet (see docs/security.md, "File uploads"); keep request bodies small.
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024

# ---------------------------------------------------------------------------
# Internationalisation: Polish-only UI, but every string goes through gettext
# so further languages can be added without touching templates (ADR 0005).
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "pl"
LANGUAGES = [("pl", _("Polski"))]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files (Tailwind is compiled by django-tailwind-cli, no Node needed)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
TAILWIND_CLI_VERSION = "4.3.3"
TAILWIND_CLI_SRC_CSS = "assets/css/source.css"
TAILWIND_CLI_DIST_CSS = "css/tailwind.css"

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_CONFIG = env.email_url("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="BartoszUP <no-reply@bartoszup.local>")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# ---------------------------------------------------------------------------
# Domain settings
# ---------------------------------------------------------------------------
LISTING_DEFAULT_LIFETIME_DAYS = env.int("LISTING_DEFAULT_LIFETIME_DAYS", default=60)
LISTINGS_PER_PAGE = 20

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
}
