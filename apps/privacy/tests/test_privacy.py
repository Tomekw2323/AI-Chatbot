import json

import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.listings.models import Inquiry, Listing
from apps.listings.services import send_inquiry
from apps.listings.tests.factories import ListingFactory
from apps.organizations.models import Membership, Organization
from apps.organizations.tests.factories import MembershipFactory, OrganizationFactory
from apps.privacy.services import AccountDeletionBlockedError, delete_account, export_user_data
from apps.profiles.models import SpecialistProfile
from apps.profiles.tests.factories import SpecialistProfileFactory

pytestmark = pytest.mark.django_db


def login_with_password(client, user: User) -> None:
    """Real login, so allauth records a recent authentication (needed for reauth views)."""
    response = client.post(reverse("account_login"), {"login": user.email, "password": "password"})
    assert response.status_code == 302


class TestExport:
    def test_contains_all_personal_data(self) -> None:
        user = UserFactory.create(first_name="Anna")
        SpecialistProfileFactory.create(user=user, bio="O mnie")
        MembershipFactory.create(user=user, job_title="Psycholog")
        listing = ListingFactory.create(author=user, title="Moje ogłoszenie")
        send_inquiry(
            listing, "Pytanie", sender=None, sender_email="gosc@example.com", sender_name="Gość"
        )
        send_inquiry(
            ListingFactory.create(published=True), "Wysłane", sender=user, sender_email=user.email
        )

        data = export_user_data(user)

        assert data["account"]["email"] == user.email
        assert data["account"]["first_name"] == "Anna"
        assert data["email_addresses"][0]["verified"] is True
        assert data["specialist_profile"]["bio"] == "O mnie"
        assert data["memberships"][0]["job_title"] == "Psycholog"
        assert data["listings"][0]["title"] == "Moje ogłoszenie"
        assert data["inquiries_sent"][0]["message"] == "Wysłane"
        assert data["inquiries_received"][0]["sender_email"] == "gosc@example.com"
        json.dumps(data)

    def test_user_without_profile(self) -> None:
        assert export_user_data(UserFactory.create())["specialist_profile"] is None

    def test_download_requires_recent_login(self, client) -> None:
        user = UserFactory.create()
        client.force_login(user)
        response = client.post(reverse("privacy:export"))
        assert response.status_code == 302
        assert "reauthenticate" in response["Location"]

    def test_download(self, client) -> None:
        user = UserFactory.create()
        login_with_password(client, user)
        response = client.post(reverse("privacy:export"))
        assert response.status_code == 200
        assert response["Content-Type"].startswith("application/json")
        assert "attachment" in response["Content-Disposition"]
        assert response["Cache-Control"] == "no-store"
        assert json.loads(response.content)["account"]["email"] == user.email

    def test_get_not_allowed_and_anonymous_redirected(self, client) -> None:
        assert client.post(reverse("privacy:export")).status_code == 302
        client.force_login(UserFactory.create())
        assert client.get(reverse("privacy:export")).status_code == 405


class TestDeleteAccountService:
    def test_deletes_personal_data(self) -> None:
        user = UserFactory.create()
        SpecialistProfileFactory.create(user=user)
        ListingFactory.create(author=user)
        send_inquiry(
            ListingFactory.create(published=True), "x", sender=user, sender_email=user.email
        )
        delete_account(user)
        assert not User.objects.filter(pk=user.pk).exists()
        assert not SpecialistProfile.objects.exists()
        assert not Listing.objects.filter(organization__isnull=True, author_id=user.pk).exists()
        assert not Inquiry.objects.filter(sender_email=user.email).exists()

    def test_sole_member_organization_is_deleted(self) -> None:
        membership = MembershipFactory.create(role=Membership.Role.OWNER)
        ListingFactory.create(author=membership.user, organization=membership.organization)
        delete_account(membership.user)
        assert not Organization.objects.exists()
        assert not Listing.objects.exists()

    def test_admin_is_promoted_and_inherits_listings(self) -> None:
        owner = MembershipFactory.create(role=Membership.Role.OWNER)
        admin = MembershipFactory.create(
            organization=owner.organization, role=Membership.Role.ADMIN
        )
        listing = ListingFactory.create(author=owner.user, organization=owner.organization)
        delete_account(owner.user)
        admin.refresh_from_db()
        listing.refresh_from_db()
        assert admin.role == Membership.Role.OWNER
        assert listing.author == admin.user

    def test_co_owner_keeps_organization(self) -> None:
        owner = MembershipFactory.create(role=Membership.Role.OWNER)
        MembershipFactory.create(organization=owner.organization, role=Membership.Role.OWNER)
        delete_account(owner.user)
        assert Organization.objects.filter(pk=owner.organization.pk).exists()

    def test_blocked_when_only_plain_members_remain(self) -> None:
        owner = MembershipFactory.create(role=Membership.Role.OWNER)
        MembershipFactory.create(organization=owner.organization, role=Membership.Role.MEMBER)
        with pytest.raises(AccountDeletionBlockedError) as exc:
            delete_account(owner.user)
        assert exc.value.organizations == [owner.organization]
        assert User.objects.filter(pk=owner.user.pk).exists()

    def test_member_listing_without_remaining_manager_is_deleted(self) -> None:
        member = MembershipFactory.create(role=Membership.Role.MEMBER)
        ListingFactory.create(author=member.user, organization=member.organization)
        delete_account(member.user)
        assert not Listing.objects.exists()


class TestDeleteAccountView:
    def test_requires_matching_email(self, client) -> None:
        user = UserFactory.create()
        login_with_password(client, user)
        response = client.post(
            reverse("privacy:delete_account"), {"confirm_email": "inny@example.com"}
        )
        assert response.status_code == 400
        assert User.objects.filter(pk=user.pk).exists()

    def test_deletes_and_logs_out(self, client) -> None:
        user = UserFactory.create()
        login_with_password(client, user)
        response = client.post(
            reverse("privacy:delete_account"), {"confirm_email": user.email.upper()}
        )
        assert response.status_code == 302
        assert not User.objects.filter(pk=user.pk).exists()
        assert "_auth_user_id" not in client.session

    def test_requires_recent_login(self, client) -> None:
        user = UserFactory.create()
        client.force_login(user)
        response = client.post(reverse("privacy:delete_account"), {"confirm_email": user.email})
        assert "reauthenticate" in response["Location"]
        assert User.objects.filter(pk=user.pk).exists()

    def test_blocked_deletion_shows_message(self, client) -> None:
        owner = MembershipFactory.create(
            role=Membership.Role.OWNER, organization=OrganizationFactory.create(name="Poradnia X")
        )
        MembershipFactory.create(organization=owner.organization, role=Membership.Role.MEMBER)
        login_with_password(client, owner.user)
        response = client.post(
            reverse("privacy:delete_account"), {"confirm_email": owner.user.email}, follow=True
        )
        assert "Poradnia X" in response.content.decode()
        assert User.objects.filter(pk=owner.user.pk).exists()


def test_my_data_page(client) -> None:
    assert client.get(reverse("privacy:my_data")).status_code == 302
    client.force_login(UserFactory.create())
    assert client.get(reverse("privacy:my_data")).status_code == 200


@pytest.mark.parametrize("name", ["privacy:terms", "privacy:policy"])
def test_legal_pages_are_public(client, name: str) -> None:
    response = client.get(reverse(name))
    assert response.status_code == 200
    assert "Wersja robocza" in response.content.decode()


def test_footer_links_legal_pages(client) -> None:
    content = client.get(reverse("home")).content.decode()
    assert reverse("privacy:terms") in content
    assert reverse("privacy:policy") in content
