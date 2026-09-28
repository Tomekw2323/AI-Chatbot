"""Template tags that let lower-level pages (organization, profile) show listings.

Lower modules must not import ``listings`` in Python code; templates compose
modules instead, which keeps the dependency direction one-way.
"""

from typing import Any

from django import template

from apps.accounts.models import User
from apps.organizations.models import Organization

from ..models import Listing

register = template.Library()


@register.inclusion_tag("listings/_listing_compact_list.html")
def organization_listings(organization: Organization) -> dict[str, Any]:
    return {
        "listings": Listing.objects.public()
        .filter(organization=organization)
        .select_related("city")[:20]
    }


@register.inclusion_tag("listings/_listing_compact_list.html")
def personal_listings(user: User) -> dict[str, Any]:
    return {
        "listings": Listing.objects.public()
        .filter(author=user, organization__isnull=True)
        .select_related("city")[:20]
    }


@register.simple_tag
def kind_badge_class(kind: str) -> str:
    classes: dict[str, str] = {
        Listing.Kind.JOB: "bg-emerald-100 text-emerald-800",
        Listing.Kind.INTERNSHIP: "bg-sky-100 text-sky-800",
        Listing.Kind.VOLUNTEERING: "bg-amber-100 text-amber-800",
        Listing.Kind.JOB_SEEKING: "bg-violet-100 text-violet-800",
        Listing.Kind.ROOM_RENTAL: "bg-rose-100 text-rose-800",
    }
    return classes.get(kind, "bg-slate-100 text-slate-800")


@register.simple_tag(takes_context=True)
def query_transform(context: dict[str, Any], **kwargs: Any) -> str:
    """Return the current query string with ``kwargs`` replaced (for pagination links)."""
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = value
    return str(query.urlencode())
