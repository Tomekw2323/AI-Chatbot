import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.core.tests.factories import CityFactory
from apps.listings.models import Inquiry, Listing
from apps.organizations.models import Membership
from apps.organizations.tests.factories import MembershipFactory, OrganizationFactory

from .factories import ListingFactory

pytestmark = pytest.mark.django_db


def test_home_page(client) -> None:
    ListingFactory.create(published=True, title="Najnowsza oferta")
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert "Najnowsza oferta" in response.content.decode()


def test_list_shows_only_public(client) -> None:
    ListingFactory.create(published=True, title="Widoczne")
    ListingFactory.create(title="Szkic")
    content = client.get(reverse("listings:list")).content.decode()
    assert "Widoczne" in content
    assert "Szkic" not in content


class TestDetail:
    def test_public_detail(self, client) -> None:
        listing = ListingFactory.create(published=True)
        assert client.get(listing.get_absolute_url()).status_code == 200

    def test_wrong_slug_redirects_to_canonical(self, client) -> None:
        listing = ListingFactory.create(published=True)
        url = reverse("listings:detail", kwargs={"pk": listing.pk, "slug": "stary-tytul"})
        response = client.get(url)
        assert response.status_code == 301
        assert response["Location"] == listing.get_absolute_url()

    def test_draft_is_404_for_others_but_visible_to_author(self, client) -> None:
        listing = ListingFactory.create()
        assert client.get(listing.get_absolute_url()).status_code == 404
        client.force_login(listing.author)
        assert client.get(listing.get_absolute_url()).status_code == 200


class TestCreateAndEdit:
    def form_data(self, city_pk: int, **overrides: str) -> dict[str, str]:
        data = {
            "kind": "job",
            "title": "Psycholog w poradni",
            "description": "Opis",
            "city": str(city_pk),
            "salary_min": "5000",
            "salary_max": "7000",
            "salary_period": "month",
            "availability-TOTAL_FORMS": "0",
            "availability-INITIAL_FORMS": "0",
            "action": "save",
        }
        data.update(overrides)
        return data

    def test_login_required(self, client) -> None:
        response = client.get(reverse("listings:create"))
        assert response.status_code == 302

    def test_create_draft(self, client) -> None:
        user = UserFactory.create()
        client.force_login(user)
        response = client.post(reverse("listings:create"), self.form_data(CityFactory.create().pk))
        listing = Listing.objects.get()
        assert response.status_code == 302
        assert listing.author == user
        assert listing.status == Listing.Status.DRAFT

    def test_create_and_publish(self, client) -> None:
        client.force_login(UserFactory.create())
        client.post(
            reverse("listings:create"), self.form_data(CityFactory.create().pk, action="publish")
        )
        assert Listing.objects.get().status == Listing.Status.PUBLISHED

    def test_kind_irrelevant_fields_are_cleared(self, client) -> None:
        client.force_login(UserFactory.create())
        data = self.form_data(
            CityFactory.create().pk, kind="volunteering", price_amount="40", price_unit="hour"
        )
        client.post(reverse("listings:create"), data)
        listing = Listing.objects.get()
        assert listing.salary_min is None
        assert listing.price_amount is None
        assert listing.price_unit == ""

    def test_room_rental_with_availability_blocks(self, client) -> None:
        client.force_login(UserFactory.create())
        data = self.form_data(
            CityFactory.create().pk,
            kind="room_rental",
            price_amount="45",
            price_unit="hour",
            **{
                "availability-TOTAL_FORMS": "1",
                "availability-0-weekday": "1",
                "availability-0-start_time": "16:00",
                "availability-0-end_time": "20:00",
            },
        )
        response = client.post(reverse("listings:create"), data)
        assert response.status_code == 302
        listing = Listing.objects.get()
        assert listing.availability_blocks.count() == 1

    def test_cannot_post_for_foreign_organization(self, client) -> None:
        client.force_login(UserFactory.create())
        foreign = OrganizationFactory.create()
        data = self.form_data(CityFactory.create().pk, organization=str(foreign.pk))
        response = client.post(reverse("listings:create"), data)
        assert response.status_code == 200
        assert "organization" in response.context["form"].errors
        assert not Listing.objects.exists()

    def test_can_post_for_managed_organization(self, client) -> None:
        membership = MembershipFactory.create(role=Membership.Role.ADMIN)
        client.force_login(membership.user)
        data = self.form_data(CityFactory.create().pk, organization=str(membership.organization.pk))
        client.post(reverse("listings:create"), data)
        assert Listing.objects.get().organization == membership.organization

    def test_stranger_cannot_edit(self, client) -> None:
        listing = ListingFactory.create()
        client.force_login(UserFactory.create())
        assert client.get(reverse("listings:update", kwargs={"pk": listing.pk})).status_code == 403

    def test_org_admin_can_edit_colleagues_listing(self, client) -> None:
        membership = MembershipFactory.create(role=Membership.Role.ADMIN)
        listing = ListingFactory.create(organization=membership.organization)
        client.force_login(membership.user)
        assert client.get(reverse("listings:update", kwargs={"pk": listing.pk})).status_code == 200


class TestTransitions:
    def url(self, listing: Listing, action: str) -> str:
        return reverse("listings:transition", kwargs={"pk": listing.pk, "action": action})

    def test_author_can_publish_and_archive(self, client) -> None:
        listing = ListingFactory.create()
        client.force_login(listing.author)
        client.post(self.url(listing, "publish"))
        listing.refresh_from_db()
        assert listing.status == Listing.Status.PUBLISHED
        client.post(self.url(listing, "archive"))
        listing.refresh_from_db()
        assert listing.status == Listing.Status.ARCHIVED

    def test_invalid_transition_is_rejected_gracefully(self, client) -> None:
        listing = ListingFactory.create(status=Listing.Status.ARCHIVED)
        client.force_login(listing.author)
        response = client.post(self.url(listing, "publish"))
        assert response.status_code == 302
        listing.refresh_from_db()
        assert listing.status == Listing.Status.ARCHIVED

    def test_get_not_allowed_and_stranger_forbidden(self, client) -> None:
        listing = ListingFactory.create()
        client.force_login(UserFactory.create())
        assert client.get(self.url(listing, "publish")).status_code == 405
        assert client.post(self.url(listing, "publish")).status_code == 403


class TestInquiry:
    def test_sends_email_with_reply_to(self, client) -> None:
        listing = ListingFactory.create(published=True, contact_email="rekrutacja@example.com")
        sender = UserFactory.create(email="kandydat@example.com")
        client.force_login(sender)
        response = client.post(
            reverse("listings:inquiry", kwargs={"pk": listing.pk}), {"message": "Dzień dobry!"}
        )
        assert response.status_code == 302
        inquiry = Inquiry.objects.get()
        assert inquiry.email_sent
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["rekrutacja@example.com"]
        assert mail.outbox[0].reply_to == ["kandydat@example.com"]
        assert "Dzień dobry!" in mail.outbox[0].body

    def test_falls_back_to_author_email(self, client) -> None:
        listing = ListingFactory.create(published=True)
        client.force_login(UserFactory.create())
        client.post(reverse("listings:inquiry", kwargs={"pk": listing.pk}), {"message": "Hej"})
        assert mail.outbox[0].to == [listing.author.email]

    def test_anonymous_redirected_to_login(self, client) -> None:
        listing = ListingFactory.create(published=True)
        response = client.post(
            reverse("listings:inquiry", kwargs={"pk": listing.pk}), {"message": "x"}
        )
        assert response.status_code == 302
        assert not Inquiry.objects.exists()

    def test_cannot_message_own_or_unpublished_listing(self, client) -> None:
        own = ListingFactory.create(published=True)
        client.force_login(own.author)
        url = reverse("listings:inquiry", kwargs={"pk": own.pk})
        assert client.post(url, {"message": "x"}).status_code == 403
        draft = ListingFactory.create()
        url = reverse("listings:inquiry", kwargs={"pk": draft.pk})
        assert client.post(url, {"message": "x"}).status_code == 403


def test_dashboard_lists_own_and_org_listings(client) -> None:
    membership = MembershipFactory.create(role=Membership.Role.OWNER)
    own = ListingFactory.create(author=membership.user, title="Moje")
    org = ListingFactory.create(organization=membership.organization, title="Firmowe")
    ListingFactory.create(title="Cudze")
    client.force_login(membership.user)
    response = client.get(reverse("dashboard"))
    assert set(response.context["listings"]) == {own, org}


def test_sitemap_and_robots(client) -> None:
    listing = ListingFactory.create(published=True)
    sitemap = client.get("/sitemap.xml").content.decode()
    assert listing.get_absolute_url() in sitemap
    assert client.get("/robots.txt").status_code == 200
