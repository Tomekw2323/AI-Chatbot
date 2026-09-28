import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.factories import CityFactory
from apps.organizations.models import Membership, Organization
from apps.organizations.services import (
    can_manage_organization,
    create_organization,
    managed_organizations,
)

from .factories import MembershipFactory, OrganizationFactory

pytestmark = pytest.mark.django_db


def test_slug_is_generated_and_unique() -> None:
    first = OrganizationFactory.create(name="Centrum Psychologii Łódź")
    second = OrganizationFactory.create(name="Centrum Psychologii Łódź")
    assert first.slug == "centrum-psychologii-lodz"
    assert second.slug == "centrum-psychologii-lodz-2"


def test_public_queryset_hides_blocked_and_private() -> None:
    visible = OrganizationFactory.create()
    OrganizationFactory.create(is_blocked=True)
    OrganizationFactory.create(is_public=False)
    assert list(Organization.objects.public()) == [visible]


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (Membership.Role.OWNER, True),
        (Membership.Role.ADMIN, True),
        (Membership.Role.MEMBER, False),
    ],
)
def test_can_manage_depends_on_role(role: str, expected: bool) -> None:
    membership = MembershipFactory.create(role=role)
    assert can_manage_organization(membership.user, membership.organization) is expected
    assert (membership.organization in managed_organizations(membership.user)) is expected


def test_outsider_and_anonymous_cannot_manage() -> None:
    from django.contrib.auth.models import AnonymousUser

    organization = OrganizationFactory.create()
    assert not can_manage_organization(UserFactory.create(), organization)
    assert not can_manage_organization(AnonymousUser(), organization)


def test_create_organization_makes_creator_owner() -> None:
    user = UserFactory.create()
    organization = create_organization(
        Organization(name="Nowa", city=CityFactory.create()), owner=user
    )
    membership = Membership.objects.get(organization=organization)
    assert membership.user == user
    assert membership.role == Membership.Role.OWNER


def test_create_view_creates_owned_organization(client) -> None:
    user = UserFactory.create()
    city = CityFactory.create()
    client.force_login(user)
    response = client.post(
        reverse("organizations:create"),
        {"name": "Poradnia Test", "kind": "clinic", "city": city.pk, "is_public": "on"},
    )
    organization = Organization.objects.get(name="Poradnia Test")
    assert response.status_code == 302
    assert can_manage_organization(user, organization)


def test_update_view_forbidden_for_plain_member(client) -> None:
    membership = MembershipFactory.create(role=Membership.Role.MEMBER)
    client.force_login(membership.user)
    url = reverse("organizations:update", kwargs={"slug": membership.organization.slug})
    assert client.get(url).status_code == 403


def test_update_view_allowed_for_admin(client) -> None:
    membership = MembershipFactory.create(role=Membership.Role.ADMIN)
    client.force_login(membership.user)
    url = reverse("organizations:update", kwargs={"slug": membership.organization.slug})
    assert client.get(url).status_code == 200
