"""Cloudflare Turnstile verification (ADR 0013).

Guests can only use forms protected by Turnstile when both keys are configured;
without keys those forms are disabled rather than left unprotected.
"""

import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TOKEN_FIELD = "cf-turnstile-response"  # noqa: S105 - form field name, not a secret


def is_enabled() -> bool:
    return bool(settings.TURNSTILE_SITE_KEY and settings.TURNSTILE_SECRET_KEY)


def verify(token: str, remote_ip: str | None = None) -> bool:
    if not (is_enabled() and token):
        return False
    payload = {"secret": settings.TURNSTILE_SECRET_KEY, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip
    request = urllib.request.Request(
        VERIFY_URL, data=urllib.parse.urlencode(payload).encode(), method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # noqa: S310
            result = json.load(response)
    except (OSError, ValueError):
        logger.warning("Turnstile verification request failed")
        return False
    return bool(result.get("success"))
