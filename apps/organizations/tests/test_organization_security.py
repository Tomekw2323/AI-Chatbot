import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.factories import CityFactory
from apps.organizations.models import Membership, Organization
from apps.organizations.services import managed_organizations

from .factories import MembershipFactory, OrganizationFactory

pytestmark = pytest.mark.django_db


def org_form(city_pk: int, **overrides: str) -> dict[str, str]:
    return {"name": "Poradnia", "kind": "clinic", "city": str(city_pk), **overrides}


def test_detail_shows_manage_links_only_to_managers(client) -> None:
    membership = MembershipFactory.create(role=Membership.Role.OWNER)
    url = membership.organization.get_absolute_url()
    edit_url = reverse("organizations:update", kwargs={"slug": membership.organization.slug})
    assert edit_url not in client.get(url).content.decode()
    client.force_login(membership.user)
    assert edit_url in client.get(url).content.decode()


def test_blocked_or_private_organization_is_404(client) -> None:
    for organization in (
        OrganizationFactory.create(is_blocked=True),
        OrganizationFactory.create(is_public=False),
    ):
        assert client.get(organization.get_absolute_url()).status_code == 404


def test_admin_can_update(client) -> None:
    membership = MembershipFactory.create(role=Membership.Role.ADMIN)
    client.force_login(membership.user)
    url = reverse("organizations:update", kwargs={"slug": membership.organization.slug})
    response = client.post(url, org_form(membership.organization.city_id, name="Nowa nazwa"))
    assert response.status_code == 302
    membership.organization.refresh_from_db()
    assert membership.organization.name == "Nowa nazwa"


def test_verification_and_blocking_cannot_be_self_assigned(client) -> None:
    membership = MembershipFactory.create(role=Membership.Role.OWNER)
    organization = membership.organization
    Organization.objects.filter(pk=organization.pk).update(is_blocked=True)
    client.force_login(membership.user)
    url = reverse("organizations:update", kwargs={"slug": organization.slug})
    client.post(url, org_form(organization.city_id, is_verified="on", is_blocked=""))
    organization.refresh_from_db()
    assert organization.is_verified is False
    assert organization.is_blocked is True


def test_create_requires_verified_email(client) -> None:
    client.force_login(UserFactory.create(verified=False))
    client.post(reverse("organizations:create"), org_form(CityFactory.create().pk))
    assert not Organization.objects.exists()


def test_create_is_rate_limited(client, settings) -> None:
    settings.RATE_LIMITS = {**settings.RATE_LIMITS, "organization_create": "1/d/user"}
    client.force_login(UserFactory.create())
    city = CityFactory.create()
    assert client.post(reverse("organizations:create"), org_form(city.pk)).status_code == 302
    assert client.post(reverse("organizations:create"), org_form(city.pk)).status_code == 429


def test_website_must_be_http(client) -> None:
    client.force_login(UserFactory.create())
    data = org_form(CityFactory.create().pk, website="javascript:alert(1)")
    response = client.post(reverse("organizations:create"), data)
    assert "website" in response.context["form"].errors


def test_managed_organizations_empty_for_anonymous() -> None:
    assert not managed_organizations(AnonymousUser()).exists()


def test_str_representations() -> None:
    membership = MembershipFactory.create(role=Membership.Role.ADMIN)
    assert str(membership.organization) == membership.organization.name
    assert "Administrator" in str(membership)
