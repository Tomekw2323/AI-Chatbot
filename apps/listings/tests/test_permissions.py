import pytest
from django.contrib.auth.models import AnonymousUser

from apps.accounts.tests.factories import UserFactory
from apps.listings.permissions import (
    can_edit_listing,
    can_post_for_organization,
    can_send_inquiry,
    can_view_listing,
)
from apps.organizations.models import Membership
from apps.organizations.tests.factories import MembershipFactory

from .factories import ListingFactory

pytestmark = pytest.mark.django_db


def test_author_can_edit_and_view_draft() -> None:
    listing = ListingFactory.create()
    assert can_edit_listing(listing.author, listing)
    assert can_view_listing(listing.author, listing)


def test_stranger_and_anonymous_cannot_edit_or_see_draft() -> None:
    listing = ListingFactory.create()
    for user in (UserFactory.create(), AnonymousUser()):
        assert not can_edit_listing(user, listing)
        assert not can_view_listing(user, listing)


def test_anyone_can_view_published() -> None:
    listing = ListingFactory.create(published=True)
    assert can_view_listing(AnonymousUser(), listing)


@pytest.mark.parametrize(
    ("role", "expected"),
    [(Membership.Role.OWNER, True), (Membership.Role.ADMIN, True), (Membership.Role.MEMBER, False)],
)
def test_organization_managers_can_edit_org_listings(role: str, expected: bool) -> None:
    membership = MembershipFactory.create(role=role)
    listing = ListingFactory.create(organization=membership.organization)
    assert can_edit_listing(membership.user, listing) is expected
    assert can_post_for_organization(membership.user, membership.organization) is expected


def test_inquiry_rules() -> None:
    listing = ListingFactory.create(published=True)
    assert can_send_inquiry(UserFactory.create(), listing)
    assert not can_send_inquiry(AnonymousUser(), listing)
    assert not can_send_inquiry(listing.author, listing)
    assert not can_send_inquiry(UserFactory.create(), ListingFactory.create())
