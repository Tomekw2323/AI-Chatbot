"""Site-wide security controls (see docs/security.md)."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.test import Client

pytestmark = pytest.mark.django_db

BASE_DIR = Path(settings.BASE_DIR)


class TestHeaders:
    @pytest.fixture
    def response(self, client):
        return client.get("/")

    def test_content_security_policy(self, response) -> None:
        policy = response.headers["Content-Security-Policy"]
        directives = dict(
            part.strip().split(" ", 1) for part in policy.split(";") if " " in part.strip()
        )
        assert directives["default-src"] == "'self'"
        assert "'unsafe-inline'" not in directives["script-src"]
        assert "'unsafe-eval'" not in directives["script-src"]
        assert directives["frame-ancestors"] == "'none'"
        assert directives["object-src"] == "'none'"
        assert directives["base-uri"] == "'self'"

    def test_other_security_headers(self, response) -> None:
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"
        assert "camera=()" in response.headers["Permissions-Policy"]


def test_csrf_is_enforced() -> None:
    client = Client(enforce_csrf_checks=True)
    response = client.post("/konto/login/", {"login": "a@example.com", "password": "x"})
    assert response.status_code == 403


def test_csrf_and_session_cookies_are_http_only() -> None:
    assert settings.CSRF_COOKIE_HTTPONLY
    assert settings.SESSION_COOKIE_HTTPONLY


def test_password_validators_reject_weak_passwords() -> None:
    from django.contrib.auth.password_validation import validate_password
    from django.core.exceptions import ValidationError

    for weak in ("krotkie1!", "password123", "1234567890123"):
        with pytest.raises(ValidationError):
            validate_password(weak)
    validate_password("Dobre-dlugie-haslo-2026")


def test_admin_is_served_from_configured_path(client) -> None:
    response = client.get(f"/{settings.ADMIN_URL}")
    assert response.status_code == 302
    assert "/login/" in response["Location"]


def test_no_template_disables_autoescaping() -> None:
    """XSS guard: user content must always be escaped in HTML templates."""
    offenders = []
    for template in (BASE_DIR / "templates").rglob("*.html"):
        text = template.read_text(encoding="utf-8")
        if "|safe" in text or "autoescape off" in text or "mark_safe" in text:
            offenders.append(str(template.relative_to(BASE_DIR)))
    assert offenders == []


def _prod_settings(**env: str) -> subprocess.CompletedProcess[str]:
    code = (
        "import json, django; django.setup(); from django.conf import settings as s; "
        "print(json.dumps({k: getattr(s, k) for k in ["
        "'DEBUG','SESSION_COOKIE_SECURE','CSRF_COOKIE_SECURE','SECURE_SSL_REDIRECT',"
        "'SECURE_HSTS_SECONDS','SESSION_COOKIE_NAME','CSRF_COOKIE_NAME','ADMIN_URL',"
        "'TRUSTED_PROXY_COUNT','ACCOUNT_EMAIL_VERIFICATION']}))"
    )
    environment = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.prod",
        "DJANGO_SECRET_KEY": "x" * 60,
        "DJANGO_ALLOWED_HOSTS": "example.com",
        **env,
    }
    return subprocess.run(  # noqa: S603 - fixed interpreter and code
        [sys.executable, "-c", code],
        env=environment,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


def test_production_settings_are_hardened() -> None:
    result = _prod_settings(DJANGO_ADMIN_URL="zaplecze-abc123/")
    assert result.returncode == 0, result.stderr
    values = json.loads(result.stdout)
    assert values["DEBUG"] is False
    assert values["SESSION_COOKIE_SECURE"] and values["CSRF_COOKIE_SECURE"]
    assert values["SECURE_SSL_REDIRECT"]
    assert values["SECURE_HSTS_SECONDS"] >= 60 * 60 * 24 * 365
    assert values["SESSION_COOKIE_NAME"].startswith("__Host-")
    assert values["CSRF_COOKIE_NAME"].startswith("__Host-")
    assert values["TRUSTED_PROXY_COUNT"] == 1
    assert values["ACCOUNT_EMAIL_VERIFICATION"] == "mandatory"


@pytest.mark.parametrize("admin_url", ["admin/", "", "no-trailing-slash"])
def test_production_refuses_guessable_admin_url(admin_url: str) -> None:
    result = _prod_settings(DJANGO_ADMIN_URL=admin_url)
    assert result.returncode != 0
    assert "DJANGO_ADMIN_URL" in result.stderr


@pytest.mark.parametrize("secret", ["", "short", "change-me-to-a-long-random-string" + "x" * 30])
def test_production_requires_strong_secret_key(secret: str) -> None:
    result = _prod_settings(DJANGO_ADMIN_URL="zaplecze-abc123/", DJANGO_SECRET_KEY=secret)
    assert result.returncode != 0
    assert "DJANGO_SECRET_KEY" in result.stderr
