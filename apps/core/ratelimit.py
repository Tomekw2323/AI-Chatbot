"""Fixed-window rate limiting stored in PostgreSQL (ADR 0014).

Counters are incremented with a single ``INSERT ... ON CONFLICT DO UPDATE``, so
concurrent requests across gunicorn workers and instances are counted exactly,
without Redis. Rates are configured in ``settings.RATE_LIMITS`` so tests and
environments can tune them.
"""

import functools
import ipaddress
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from django.conf import settings
from django.db import connection
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.shortcuts import render

from .models import RateLimitCounter

PERIODS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

type View = Callable[..., HttpResponseBase]


def parse_rate(rate: str) -> tuple[int, int]:
    """``"5/h"`` -> (5, 3600); ``"10/15m"`` -> (10, 900)."""
    count, _, period = rate.partition("/")
    multiplier = int(period[:-1] or 1)
    return int(count), multiplier * PERIODS[period[-1]]


def client_ip(request: HttpRequest) -> str:
    """Client IP, honouring ``TRUSTED_PROXY_COUNT`` entries of X-Forwarded-For.

    Only the entry appended by our own proxy is trusted; anything to its left can
    be forged by the client.
    """
    proxies: int = settings.TRUSTED_PROXY_COUNT
    forwarded = request.headers.get("x-forwarded-for", "")
    candidate = request.META.get("REMOTE_ADDR", "")
    if proxies and forwarded:
        hops = [part.strip() for part in forwarded.split(",")]
        if len(hops) >= proxies:
            candidate = hops[-proxies]
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return "unknown"


def hit(key: str, rate: str, now: datetime | None = None) -> bool:
    """Count one event for ``key``; return False when the rate is exceeded."""
    limit, period = parse_rate(rate)
    timestamp = int((now or datetime.now(UTC)).timestamp())
    window_start = datetime.fromtimestamp(timestamp - timestamp % period, tz=UTC)
    table = RateLimitCounter._meta.db_table
    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            INSERT INTO {table} (key, window_start, period_seconds, count)
            VALUES (%s, %s, %s, 1)
            ON CONFLICT (key, window_start, period_seconds)
            DO UPDATE SET count = {table}.count + 1
            RETURNING count
            """,  # noqa: S608 - table name comes from model metadata, values are parameters
            [key[:200], window_start, period],
        )
        (count,) = cursor.fetchone()
    return bool(count <= limit)


def rate_limited_response(request: HttpRequest) -> HttpResponse:
    return render(request, "429.html", status=429)


def ratelimit(scope: str, methods: tuple[str, ...] = ("POST",)) -> Callable[[View], View]:
    """Limit a view per user (when signed in) and per client IP.

    ``settings.RATE_LIMITS[scope]`` is a comma-separated list such as
    ``"5/h/user,20/h/ip"``; every listed limit must pass.
    """

    def decorator(view: View) -> View:
        @functools.wraps(view)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponseBase:
            if request.method in methods and not check(request, scope):
                return rate_limited_response(request)
            return view(request, *args, **kwargs)

        return wrapper

    return decorator


def check(request: HttpRequest, scope: str) -> bool:
    spec: str = settings.RATE_LIMITS.get(scope, "")
    allowed = True
    for rule in filter(None, (part.strip() for part in spec.split(","))):
        count, period, subject = rule.split("/")
        if subject == "user":
            if not request.user.is_authenticated:
                continue
            identity = f"user:{request.user.pk}"
        else:
            identity = f"ip:{client_ip(request)}"
        # Evaluate every rule so each counter reflects the attempt.
        allowed &= hit(f"{scope}:{identity}", f"{count}/{period}")
    return allowed


def purge_old_windows(older_than: timedelta = timedelta(days=2)) -> int:
    """Delete counters that can no longer affect any limit (longest period is a day)."""
    cutoff = datetime.now(UTC) - older_than
    deleted, _ = RateLimitCounter.objects.filter(window_start__lt=cutoff).delete()
    return deleted
