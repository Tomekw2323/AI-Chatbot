"""Public free demo: banner, fake samples, SQLite settings. Production stays on Postgres."""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command
from django.urls import reverse

from apps.accounts.models import User
from apps.listings.models import Listing
from apps.listings.tests.factories import ListingFactory
from apps.organizations.models import Organization
from apps.profiles.models import SpecialistProfile

pytestmark = pytest.mark.django_db

BASE_DIR = Path(settings.BASE_DIR)
BANNER = "To jest demo. Dane są wymyślone i nie jest to prawdziwa usługa."


def test_demo_banner_is_on_the_click_path(client, settings) -> None:
    settings.DEMO_MODE = True
    listing = ListingFactory.create(published=True)
    urls = [
        reverse("home"),
        reverse("listings:list"),
        listing.get_absolute_url(),
        reverse("account_signup"),
        reverse("profiles:list"),
    ]
    for url in urls:
        response = client.get(url)
        assert response.status_code == 200, url
        assert BANNER in response.content.decode()


def test_demo_banner_is_absent_by_default(client, settings) -> None:
    settings.DEMO_MODE = False
    response = client.get("/")
    assert response.status_code == 200
    assert BANNER not in response.content.decode()


def test_seed_demo_in_demo_mode_has_samples_and_no_superuser(settings) -> None:
    settings.DEBUG = False
    settings.DEMO_MODE = True
    call_command("seed_demo", stdout=None)
    call_command("seed_demo", stdout=None)
    assert not User.objects.filter(is_superuser=True).exists()
    assert SpecialistProfile.objects.filter(user__email="anna@example.com").exists()
    assert Organization.objects.filter(name="Centrum Psychologii Wrocław").exists()
    assert Listing.objects.filter(kind=Listing.Kind.JOB, city__slug="krakow").count() == 1
    assert Listing.objects.filter(kind=Listing.Kind.ROOM_RENTAL, city__slug="wroclaw").count() == 1


def test_prepare_demo_refuses_outside_demo_mode(settings) -> None:
    settings.DEMO_MODE = False
    with pytest.raises(CommandError):
        call_command("prepare_demo")


@pytest.mark.parametrize("cache_exists", [False, True])
def test_prepare_demo_startup_steps(settings, monkeypatch, cache_exists: bool) -> None:
    settings.DEMO_MODE = True
    steps: list[str] = []

    def record(name: str, *args: object, **kwargs: object) -> None:
        steps.append(name)

    monkeypatch.setattr("apps.listings.management.commands.prepare_demo.call_command", record)
    tables = ["django_cache"] if cache_exists else []
    monkeypatch.setattr(
        "apps.listings.management.commands.prepare_demo.connection.introspection.table_names",
        lambda: tables,
    )
    call_command("prepare_demo")
    expected = ["migrate", "loaddata", "seed_demo"]
    if not cache_exists:
        expected.insert(1, "createcachetable")
    assert steps == expected


def test_demo_blueprint_is_one_free_web_service() -> None:
    demo = (BASE_DIR / "render.demo.yaml").read_text(encoding="utf-8")
    production = (BASE_DIR / "render.yaml").read_text(encoding="utf-8")
    assert "plan: free" in demo
    assert "runtime: docker" in demo
    assert "databases:" not in demo
    assert "type: cron" not in demo
    assert "config.settings.demo" in demo
    assert "plan: starter" in production
    assert "basic-256mb" in production
    assert "region: frankfurt" in production


def test_demo_mode_serves_sqlite_with_fake_samples(tmp_path: Path) -> None:
    """Boot the demo settings module for real, against a throwaway SQLite file."""
    db_path = tmp_path / "demo.sqlite3"
    code = """
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.test import Client
from apps.accounts.models import User
from apps.core.ratelimit import hit
from apps.listings.models import Listing
from apps.organizations.models import Organization
from apps.profiles.models import SpecialistProfile

call_command("prepare_demo")
call_command("prepare_demo")
assert settings.DEMO_MODE is True
assert settings.DEBUG is False
assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
assert hit("demo-boot", "5/h") is True
assert not User.objects.filter(is_superuser=True).exists()
assert Listing.objects.filter(kind="job", city__slug="krakow").exists()
assert Listing.objects.filter(kind="room_rental", city__slug="wroclaw").exists()
assert SpecialistProfile.objects.filter(user__email="anna@example.com").exists()
assert Organization.objects.filter(name="Centrum Psychologii Wrocław").exists()
# The image collects hashed static files at build time. This process has not,
# so render pages with the plain storage. Deployed demo keeps the manifest.
settings.STORAGES["staticfiles"] = {
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
}
client = Client()
home = client.get("/")
assert home.status_code == 200, home.status_code
assert "To jest demo." in home.content.decode()
signup = client.get("/konto/signup/")
assert signup.status_code == 200
assert "To jest demo." in signup.content.decode()
health = client.get("/healthz/")
assert health.status_code == 200
assert health.content == b"ok"
print("ok")
"""
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": "config.settings.demo",
        "DJANGO_SECRET_KEY": "demo-test-secret-not-used-outside-this-process-0123456789",
        "DJANGO_ALLOWED_HOSTS": "testserver,localhost",
        "DJANGO_SECURE_SSL_REDIRECT": "false",
        "DEMO_SQLITE_PATH": str(db_path),
    }
    result = subprocess.run(  # noqa: S603 - fixed interpreter and code
        [sys.executable, "-c", code],
        env=env,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "ok" in result.stdout
    assert db_path.exists()
