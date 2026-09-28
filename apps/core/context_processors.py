from django.conf import settings
from django.http import HttpRequest


def site(request: HttpRequest) -> dict[str, str | bool]:
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_URL": settings.SITE_URL,
        "DEMO_MODE": settings.DEMO_MODE,
    }
