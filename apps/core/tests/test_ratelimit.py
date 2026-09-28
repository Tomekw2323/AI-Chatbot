from datetime import UTC, datetime, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from apps.core.models import RateLimitCounter
from apps.core.ratelimit import (
    check,
    client_ip,
    hit,
    parse_rate,
    purge_old_windows,
    ratelimit,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("rate", "expected"),
    [("5/h", (5, 3600)), ("10/15m", (10, 900)), ("1/s", (1, 1)), ("3/2d", (3, 172800))],
)
def test_parse_rate(rate: str, expected: tuple[int, int]) -> None:
    assert parse_rate(rate) == expected


def test_hit_allows_up_to_limit_then_blocks() -> None:
    now = datetime(2026, 1, 1, 12, 0, 30, tzinfo=UTC)
    assert [hit("k", "3/m", now) for _ in range(4)] == [True, True, True, False]
    assert RateLimitCounter.objects.get().count == 4


def test_hit_starts_new_window() -> None:
    first = datetime(2026, 1, 1, 12, 0, 59, tzinfo=UTC)
    assert hit("k", "1/m", first)
    assert not hit("k", "1/m", first)
    assert hit("k", "1/m", first + timedelta(seconds=1))


def test_keys_and_periods_are_independent() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    assert hit("a", "1/h", now)
    assert hit("b", "1/h", now)
    assert hit("a", "1/d", now)


def test_purge_old_windows() -> None:
    old = datetime.now(UTC) - timedelta(days=3)
    hit("old", "1/h", old)
    hit("fresh", "1/h")
    assert purge_old_windows() == 1
    assert list(RateLimitCounter.objects.values_list("key", flat=True)) == ["fresh"]


class TestClientIp:
    def request(self, remote: str, forwarded: str | None = None) -> HttpRequest:
        headers = {"x-forwarded-for": forwarded} if forwarded else {}
        return RequestFactory().get("/", REMOTE_ADDR=remote, headers=headers)

    def test_ignores_forwarded_header_without_trusted_proxy(self, settings) -> None:
        settings.TRUSTED_PROXY_COUNT = 0
        assert client_ip(self.request("10.0.0.1", "6.6.6.6")) == "10.0.0.1"

    def test_uses_entry_added_by_trusted_proxy(self, settings) -> None:
        settings.TRUSTED_PROXY_COUNT = 1
        # The client forged "6.6.6.6"; our proxy appended the real address.
        request = self.request("10.0.0.1", "6.6.6.6, 203.0.113.7")
        assert client_ip(request) == "203.0.113.7"

    def test_invalid_address(self, settings) -> None:
        settings.TRUSTED_PROXY_COUNT = 1
        assert client_ip(self.request("10.0.0.1", "not-an-ip")) == "unknown"


class TestDecorator:
    @pytest.fixture
    def view(self):
        @ratelimit("test_scope")
        def view(request: HttpRequest) -> HttpResponse:
            return HttpResponse("ok")

        return view

    def test_blocks_post_over_limit(self, view, settings) -> None:
        settings.RATE_LIMITS = {"test_scope": "2/h/ip"}
        factory = RequestFactory()
        codes = [view(factory.post("/", REMOTE_ADDR="1.2.3.4")).status_code for _ in range(3)]
        assert codes == [200, 200, 429]
        assert view(factory.post("/", REMOTE_ADDR="5.6.7.8")).status_code == 200

    def test_get_is_not_limited(self, view, settings) -> None:
        settings.RATE_LIMITS = {"test_scope": "1/h/ip"}
        factory = RequestFactory()
        assert all(view(factory.get("/")).status_code == 200 for _ in range(3))

    def test_user_rule_applies_per_user(self, settings) -> None:
        from django.contrib.auth.models import AnonymousUser

        settings.RATE_LIMITS = {"scope": "1/h/user"}
        factory = RequestFactory()
        first, second = factory.post("/"), factory.post("/")
        # core must not import accounts, even in tests (import-linter layers).
        first.user = second.user = get_user_model().objects.create_user("rl@example.com", "x")
        assert check(first, "scope")
        assert not check(second, "scope")
        anonymous = factory.post("/")
        anonymous.user = AnonymousUser()
        assert check(anonymous, "scope"), "user rules do not apply to anonymous requests"
