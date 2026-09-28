import io
import json
import urllib.request

import pytest

from apps.core import captcha


@pytest.fixture
def keys(settings):
    settings.TURNSTILE_SITE_KEY = "site"
    settings.TURNSTILE_SECRET_KEY = "secret"


def fake_urlopen(payload: dict[str, object], calls: list[bytes]):
    def urlopen(request: urllib.request.Request, timeout: int) -> io.BytesIO:
        assert request.full_url == captcha.VERIFY_URL
        calls.append(request.data)  # type: ignore[arg-type]
        return io.BytesIO(json.dumps(payload).encode())

    return urlopen


def test_disabled_without_keys(settings) -> None:
    settings.TURNSTILE_SITE_KEY = ""
    assert not captcha.is_enabled()
    assert not captcha.verify("token")


def test_empty_token_rejected_without_network(keys, monkeypatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", pytest.fail)
    assert not captcha.verify("")


def test_success_sends_secret_token_and_ip(keys, monkeypatch) -> None:
    calls: list[bytes] = []
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen({"success": True}, calls))
    assert captcha.verify("token", "203.0.113.7")
    assert calls == [b"secret=secret&response=token&remoteip=203.0.113.7"]


def test_failed_challenge(keys, monkeypatch) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen({"success": False}, []))
    assert not captcha.verify("token")


def test_network_error_fails_closed(keys, monkeypatch) -> None:
    def broken(*args: object, **kwargs: object) -> None:
        raise OSError("timeout")

    monkeypatch.setattr(urllib.request, "urlopen", broken)
    assert not captcha.verify("token")
