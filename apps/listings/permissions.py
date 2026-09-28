"""Who may do what with a listing. Views must go through these helpers."""

from apps.organizations.models import Organization
from apps.organizations.services import AnyUser, can_manage_organization

from .models import Listing


def can_edit_listing(user: AnyUser, listing: Listing) -> bool:
    """The author, or an owner/admin of the organization the listing belongs to."""
    if not user.is_authenticated:
        return False
    if listing.author_id == user.pk:
        return True
    return listing.organization is not None and can_manage_organization(user, listing.organization)


def can_view_listing(user: AnyUser, listing: Listing) -> bool:
    return listing.is_publicly_visible or can_edit_listing(user, listing)


def can_post_for_organization(user: AnyUser, organization: Organization) -> bool:
    return can_manage_organization(user, organization)


def can_send_inquiry(user: AnyUser, listing: Listing) -> bool:
    return user.is_authenticated and listing.is_publicly_visible and listing.author_id != user.pk
