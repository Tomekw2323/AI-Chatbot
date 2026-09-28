"""GDPR data-subject rights: access/portability (art. 15/20) and erasure (art. 17).

This module sits above all others because it has to see every piece of personal
data a user owns.
"""

from typing import Any

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.accounts.models import User
from apps.listings.models import Inquiry, Listing, ListingReport
from apps.organizations.models import Membership, Organization
from apps.profiles.models import SpecialistProfile


class AccountDeletionBlockedError(Exception):
    """Deleting would leave an organization with members but no owner."""

    def __init__(self, organizations: list[Organization]) -> None:
        super().__init__(", ".join(o.name for o in organizations))
        self.organizations = organizations


def _iso(value: Any) -> Any:
    return value.isoformat() if hasattr(value, "isoformat") else value


def _listing_data(listing: Listing) -> dict[str, Any]:
    return {
        "id": listing.pk,
        "kind": listing.kind,
        "title": listing.title,
        "description": listing.description,
        "status": listing.status,
        "organization": listing.organization.name if listing.organization else None,
        "city": listing.city.name,
        "address": listing.address,
        "contact_email": listing.contact_email,
        "created_at": _iso(listing.created_at),
        "published_at": _iso(listing.published_at),
        "expires_at": _iso(listing.expires_at),
    }


def export_user_data(user: User) -> dict[str, Any]:
    """Everything we store about ``user``, in a machine-readable structure."""
    profile = SpecialistProfile.objects.filter(user=user).first()
    listings = Listing.objects.filter(author=user).select_related("city", "organization")
    return {
        "exported_at": _iso(timezone.now()),
        "account": {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": _iso(user.date_joined),
            "last_login": _iso(user.last_login),
            "terms_accepted_at": _iso(user.terms_accepted_at),
        },
        "email_addresses": [
            {"email": e.email, "verified": e.verified, "primary": e.primary}
            for e in EmailAddress.objects.filter(user=user)
        ],
        "connected_accounts": [
            {"provider": s.provider, "date_joined": _iso(s.date_joined)}
            for s in SocialAccount.objects.filter(user=user)
        ],
        "specialist_profile": None
        if profile is None
        else {
            "slug": profile.slug,
            "academic_title": profile.academic_title,
            "profession": profile.profession,
            "headline": profile.headline,
            "bio": profile.bio,
            "city": profile.city.name,
            "works_online": profile.works_online,
            "specializations": [s.name for s in profile.specializations.all()],
            "approaches": [a.name for a in profile.approaches.all()],
            "languages": profile.languages,
            "license_number": profile.license_number,
            "contact_email": profile.contact_email,
            "contact_phone": profile.contact_phone,
            "website": profile.website,
            "open_to_work": profile.open_to_work,
            "is_public": profile.is_public,
        },
        "memberships": [
            {"organization": m.organization.name, "role": m.role, "job_title": m.job_title}
            for m in Membership.objects.filter(user=user).select_related("organization")
        ],
        "listings": [_listing_data(listing) for listing in listings],
        "inquiries_sent": [
            {
                "listing": i.listing.title,
                "message": i.message,
                "created_at": _iso(i.created_at),
            }
            for i in Inquiry.objects.filter(sender=user).select_related("listing")
        ],
        "inquiries_received": [
            {
                "listing": i.listing.title,
                "sender_name": i.sender_name,
                "sender_email": i.sender_email,
                "message": i.message,
                "created_at": _iso(i.created_at),
            }
            for i in Inquiry.objects.filter(listing__author=user).select_related("listing")
        ],
        "listing_reports": [
            {"listing": r.listing.title, "reason": r.reason, "created_at": _iso(r.created_at)}
            for r in ListingReport.objects.filter(reporter=user).select_related("listing")
        ],
    }


def _plan_organizations(user: User) -> tuple[list[Organization], list[Membership]]:
    """Return (organizations to delete, admins to promote); raise if blocked."""
    to_delete: list[Organization] = []
    to_promote: list[Membership] = []
    blocked: list[Organization] = []
    owned = Organization.objects.filter(
        memberships__user=user, memberships__role=Membership.Role.OWNER
    )
    for organization in owned:
        others = organization.memberships.exclude(user=user)
        if others.filter(role=Membership.Role.OWNER).exists():
            continue
        if not others.exists():
            to_delete.append(organization)
            continue
        successor = others.filter(role=Membership.Role.ADMIN).order_by("created_at").first()
        if successor is None:
            blocked.append(organization)
        else:
            to_promote.append(successor)
    if blocked:
        raise AccountDeletionBlockedError(blocked)
    return to_delete, to_promote


@transaction.atomic
def delete_account(user: User) -> None:
    """Erase the user and their personal data.

    - Organizations where they are the only member are deleted with their listings.
    - Ownership passes to the longest-standing admin; with members but no admin the
      deletion is blocked so an organization is never left without a manager.
    - Their organization listings stay with the organization (re-assigned to an
      owner); personal listings, profile, memberships and sent inquiries are deleted.
    """
    to_delete, to_promote = _plan_organizations(user)
    for membership in to_promote:
        membership.role = Membership.Role.OWNER
        membership.save(update_fields=["role", "updated_at"])
    for organization in to_delete:
        organization.delete()

    for listing in Listing.objects.filter(author=user, organization__isnull=False):
        assert listing.organization is not None  # noqa: S101 - guaranteed by the filter
        new_owner = (
            listing.organization.memberships.exclude(user=user)
            .filter(role__in=Membership.MANAGER_ROLES)
            .order_by("-role", "created_at")
            .first()
        )
        if new_owner is None:
            listing.delete()
        else:
            listing.author_id = new_owner.user_id
            listing.save(update_fields=["author", "updated_at"])

    Inquiry.objects.filter(Q(sender=user) | Q(sender_email__iexact=user.email)).delete()
    user.delete()
